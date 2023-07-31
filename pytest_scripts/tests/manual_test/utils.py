import logging
import random
import re
import string
import subprocess
import time

import cup
import requests

cpu_per_task = 4
gpu_per_task = 0

logger = logging.getLogger("cluster.utils")


def gen_uni_name(str_value=None):
    random_str = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
    return random_str if str_value is None else str_value + "_" + random_str


def retry(times, interval=3):
    """
    This decorator prints the execution time for the decorated function.
    """

    def wrapper(func):
        def newfn(*args, **kwargs):
            t = 0
            result = False
            while t < times:
                try:
                    result = func(*args, **kwargs)
                    if result:
                        break
                    else:
                        logger.warning(result)
                        logger.warning("Retry %d times", t)
                        time.sleep(interval)
                        t += 1
                except Exception as e:  # pylint: disable=W0703
                    logger.error(str(e))
                    logger.warning("Retry %d times", t)
                    time.sleep(interval)
                    t += 1
            return result

        return newfn

    return wrapper


def call_command(command, break_condition, break_param=None, retry_times=1, wait_time=1):
    for _ in range(retry_times):
        execute_result = subprocess.Popen(  # pylint: disable=R1732
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        result = execute_result.stdout.read().decode().rstrip("\n")
        execute_result.stdout.close()
        result = re.sub("\x1b.*?m", "", result)
        exec_param = {"result_bool": False, "result": result, "param": break_param}
        exec(break_condition, exec_param)  # pylint: disable=exec-used
        if exec_param["result_bool"]:
            break
        time.sleep(wait_time)
    exec_param = {"result_bool": exec_param["result_bool"], "result": exec_param["result"]}
    return exec_param


def ip_parser(hostname):
    if hostname:
        return ".".join(hostname.split("-")[-4:])
    return ""


class RayHTTPClient:
    """send request to ray"""

    def __init__(self, uri):
        self.uri = uri

    @retry(3)
    def get(self, url):
        url = self.uri + url
        logger.debug(url)
        try:
            # TODO:
            time.sleep(15)
            # pdb.set_trace()
            return requests.get(url).json()
        except Exception as e:  # pylint: disable=W0703
            logger.error(str(e))
            return None


class Slurm:
    """a simple slurm wrapper"""

    def __init__(self, cluster_addr=None, user=None):
        # cluster addr
        self.cluster_addr = cluster_addr
        self.user = user

    def _run_command(self, cmd, timeout=10):
        """
        return {
            'stdout' : 'Success',
            'stderr' : None,
            'returncode' : 0
        }
        returncode == 0 means success, while 999 means timeout
        """
        shelltool = cup.shell.ShellExec()
        cmd_res = shelltool.run(cmd, timeout=timeout)
        if "stderr" in cmd_res and cmd_res["stderr"]:
            logger.error(cmd_res)
        return cmd_res

    def scancel(self, job_id):
        res = self._run_command(f"scancel {job_id}")
        if res["returncode"] == 0:
            logger.debug("Scancel job: %s success.", job_id)

    def sbatch(self, job_name, partition_name, **kargs):
        join_params = f"sbatch -p {partition_name} --job-name={job_name} "
        logger.debug(kargs)
        batch_type = "head"
        # TODO: need to check
        if "head_node_addr" in kargs and kargs["head_node_addr"]:
            batch_type = "worker"
            node_kargs = kargs["compute_node"]
        else:
            node_kargs = kargs["head_node"]
        if "include" in node_kargs and node_kargs["include"] != "":
            join_params += f"-w {node_kargs['include']} "
        if "exclude" in node_kargs and node_kargs["exclude"] != "":
            join_params += f"-x {node_kargs['exclude']} "
        if "exclusive" in node_kargs and node_kargs["exclusive"] is True:
            join_params += "--exclusive "
        if "cpu_per_task" in node_kargs:
            join_params += f"--cpus-per-task={node_kargs['cpu_per_task']} "
        if "gpu_per_task" in node_kargs:
            join_params += f"--gpus-per-task={node_kargs['gpu_per_task']} "
        if "nodes" in node_kargs and node_kargs["nodes"]:
            join_params += f"--nodes={node_kargs['nodes']} "
        # TODO: partition name need to added
        # ray worker node
        if batch_type == "worker":
            join_params += node_kargs["script_path"]
            join_params += f" -h {kargs['head_node_addr']} "
        # ray head node
        else:
            join_params += node_kargs["script_path"]
        logger.debug(join_params)
        return self._run_command(join_params)

    def get_job_status(self, job_name):
        job = self.get_job(job_name)
        return job["STATE"] if job else None

    # return job dict
    def get_job(self, job_name):
        job = None
        # format:
        # JOBID|ARRAY_TASK_ID|CPUS|TRES_PER_NODE|NAME|VIRTUAL_PARTITION|REASON|USER|NICE|
        # STATE|TIME|TRES_PER_NODE|NODELIST
        cmd = f"squeue -n {job_name}" + ' -o "%A|%K|%C|%b|%j|%P|%r|%u|%y|%T|%M|%b|%N"'
        o = self._run_command(cmd)
        if o["returncode"]:
            return job
        res = o["stdout"].strip().split("\n")
        logger.debug(res)
        if len(res) == 1:
            logger.error("No job found by name: %s", job_name)
            return job
        elif len(res) > 2:
            logger.error("At least one job found by name: %s", job_name)
            return job
        fields = res[0].split("|")
        return {k: v for k, v in zip(fields, res[1].split("|"))}  # pylint: disable=R1721

    def is_running(self, job_name, timeout=60, time_interval=1):
        st = time.time()
        while time.time() - st < timeout:
            # TODO: add job status
            job_status = self.get_job_status(job_name)
            logger.debug(job_status)
            if job_status != "RUNNING":
                time.sleep(time_interval)
                continue
            else:
                logger.debug("Job running...")
            return True
        return False

    def wait_job_finished(self, job_name, timeout=60, time_interval=1):
        st = time.time()
        while time.time() - st < timeout:
            # TODO: add job status
            job_status = self.get_job_status(job_name)
            logger.debug(job_status)
            if job_status != "COMPLETED":
                time.sleep(time_interval)
                continue
            else:
                logger.debug("Job finished")
            return True
        return False
