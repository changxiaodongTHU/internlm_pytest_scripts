import copy
import logging
import os
import time
import traceback

import yaml

import uniscale
from tests.common import utils

RAY_HEAD_JOB_NAME = "ray_head_job_"
RAY_WORKER_JOB_NAME = "ray_worker_job_"
RAY_CLUSTER_PORT = "8265"
LOG_FOLDER = "./"

logger = logging.getLogger("cluster")
formatter = logging.Formatter("[%(asctime)s] [%(levelname)-4s] [%(pathname)s:%(lineno)d] %(message)s")
fileTimeHandler = logging.handlers.TimedRotatingFileHandler(os.path.join(LOG_FOLDER, "test.out"), "D", 1, 10)
fileTimeHandler.suffix = "%Y%m%d.log"
fileTimeHandler.setFormatter(formatter)
logging.basicConfig(level=logging.DEBUG)
fileTimeHandler.setFormatter(formatter)
logger.addHandler(fileTimeHandler)


class RayCluster:
    """start ray cluster and check status"""

    def __init__(self, cluster_params):
        # TODO: cluster addr for slurm
        self.slurm_client = utils.Slurm()
        self.cluster_params = cluster_params
        self.ray_cluster = {}

    @property
    def ray_cluster_info(self):
        return self.ray_cluster

    # check ray head status from `api/cluster_status`
    def check_head_status(self):
        # TODO: may be not work with the new version of ray
        # TODO: ray.is_initialized()
        url = "api/cluster_status"
        if "head_node_addr" not in self.ray_cluster or not self.ray_cluster["head_node_addr"]:
            return False
        http_client = utils.RayHTTPClient(f"http://{self.ray_cluster['head_node_addr']}:{RAY_CLUSTER_PORT}/")
        res = http_client.get(url)
        if res and res["result"] is True:
            return True
        return False

    # check ray worker status from `nodes`
    def check_worker_status(self):
        # TODO: other implemention
        url = "nodes?view=summary"
        ray_live_node = []
        http_client = utils.RayHTTPClient(f"http://{self.ray_cluster['head_node_addr']}:{RAY_CLUSTER_PORT}/")
        res = http_client.get(url)
        if not res or not res["data"]:
            return False
        for i in range(len(res["data"]["summary"])):
            if res["data"]["summary"][i]["raylet"]["state"] == "ALIVE":
                if res["data"]["summary"][i]["raylet"]["nodeName"] != self.ray_cluster["head_node_addr"]:
                    ray_live_node.append(res["data"]["summary"][i]["raylet"]["nodeName"])
        if len(ray_live_node) < self.cluster_params["compute_node"]["nodes"]:
            return False
        return ray_live_node

    # Not work with S-cluster
    # def start_head_node_with_sdk(self):
    #     job_params = {
    #         "job_name": RAY_HEAD_JOB_NAME,
    #         "partition": self.cluster_params["head_node"]["partition"],
    #         "cpu_per_task": self.cluster_params["head_node"]["cpu_per_task"],
    #         "gpu_per_task": self.cluster_params["head_node"]["gpu_per_task"],
    #     }
    #     # TODO: need to check
    #     if self.cluster_params["head_node"]["include"] != "":
    #         job_params["include"] = self.cluster_params["head_node"]["include"]
    #     if self.cluster_params["head_node"]["exclude"] != "":
    #         job_params["exclude"] = self.cluster_params["head_node"]["exclude"]
    #     if self.cluster_params["head_node"]["exclusive"] is True:
    #         job_params["exclusive"] = True

    #     res = self.slurm_client.sbatch(job_params, wait_finished=True)
    #     if res:
    #         pass

    # TODO: slurm-sdk is prefered: `https://github.com/PySlurm/pyslurm`, but not supported on S/S1/.. cluster.
    # return True/False
    def start_head_node(self):
        start_status = False
        job_id = None
        job_name = utils.gen_uni_name(RAY_HEAD_JOB_NAME)
        try:
            res = self.slurm_client.sbatch(
                job_name, self.cluster_params["head_node"]["partition"], **self.cluster_params
            )
            logger.debug(res)
            if not self.slurm_client.is_running(job_name, timeout=60):  # 60s
                logger.warning("Head not is not running.")
                logger.debug(self.slurm_client.get_job(job_name))
                job_id = self.slurm_client.get_job(job_name)["JOBID"]
                self.slurm_client.scancel(job_id)
            else:
                job = self.slurm_client.get_job(job_name)
                head_node_addr = job["NODELIST"]
                logger.debug(head_node_addr)

                if head_node_addr:
                    self.ray_cluster["head_node_addr"] = utils.ip_parser(head_node_addr)
                if self.check_head_status():
                    logger.debug("Head node started.")
                    start_status = True
                    self.ray_cluster["head_job_id"] = job["JOBID"]
                else:
                    logger.error("Head node status no OK.")
                    if job_id:
                        self.slurm_client.scancel(job_id)
        except Exception:  # pylint: disable=W0703
            logger.error(traceback.format_exc())
            if job_id:
                self.slurm_client.scancel(job_id)
        finally:
            return start_status  # pylint: disable=W0150

    def shutdown(self):
        job_ids = []
        if "head_job_id" in self.ray_cluster and self.ray_cluster["head_job_id"]:
            job_ids.append(self.ray_cluster["head_job_id"])
        if "worker_job_id" in self.ray_cluster and self.ray_cluster["worker_job_id"]:
            job_ids.append(self.ray_cluster["worker_job_id"])
        logger.debug(job_ids)
        for job_id in job_ids:
            self.slurm_client.scancel(job_id)

    # TODO: use slurm python-sdk/slurm wrapper in `utils.py`
    def start_worker_node(self):
        start_status = False
        job_id = None
        job_name = utils.gen_uni_name(RAY_WORKER_JOB_NAME)
        try:
            worker_params = copy.deepcopy(self.cluster_params)
            worker_params["head_node_addr"] = self.ray_cluster["head_node_addr"]
            res = self.slurm_client.sbatch(job_name, self.cluster_params["compute_node"]["partition"], **worker_params)
            logger.debug(res)
            if not self.slurm_client.is_running(job_name, timeout=60):  # 60s
                logger.warning("Worker node is not running.")
                logger.debug(self.slurm_client.get_job(job_name))
                job_id = self.slurm_client.get_job(job_name)["JOBID"]
                self.slurm_client.scancel(job_id)
            else:
                job = self.slurm_client.get_job(job_name)
                job_id = job["JOBID"]
                logger.debug(job["NODELIST"])
                for _ in range(60):
                    worker_node_addr = self.check_worker_status()
                    if worker_node_addr:
                        break
                    time.sleep(1)
                if worker_node_addr:
                    self.ray_cluster["worker_node_addr"] = worker_node_addr
                    start_status = True
                    self.ray_cluster["worker_job_id"] = job["JOBID"]
                else:
                    logger.error("Worker node status no OK.")
                    if job_id:
                        self.slurm_client.scancel(job_id)
        except Exception:  # pylint: disable=W0703
            logger.error(traceback.format_exc())
            if job_id:
                self.slurm_client.scancel(job_id)
        finally:
            return start_status  # pylint: disable=W0150


class UniscaleCluster:
    """get ray cluster info"""

    def __init__(self, env_file_yaml=None):
        self.cluster_params = None
        self.ray_cluster = None
        self.cluster_info = {"head_node_addr": None, "worker_node_addr": None}
        if env_file_yaml is not None:
            try:
                with open(env_file_yaml, "r", encoding="utf-8") as f:
                    self.cluster_params = yaml.safe_load(f)
                    self.ray_cluster = RayCluster(self.cluster_params)
            except Exception as e:
                logger.error(self.cluster_params)
                raise Exception(str(e)) from e

    def install(self):
        if self.ray_cluster is not None:
            if not self.ray_cluster.start_head_node():
                return self.cluster_info
            if self.ray_cluster.ray_cluster_info["head_node_addr"]:
                self.cluster_info["head_node_addr"] = self.ray_cluster.ray_cluster_info["head_node_addr"]
            if not self.ray_cluster.start_worker_node():
                return self.cluster_info
            if self.ray_cluster.ray_cluster_info["worker_node_addr"]:
                self.cluster_info["worker_node_addr"] = self.ray_cluster.ray_cluster_info["worker_node_addr"]
            else:
                return self.cluster_info
        else:
            # return None if no env_file specified
            from uniscale._internal import _is_initialized

            if _is_initialized() is True:
                # a new instance will be initialized after calling `shutdown`?
                uniscale.shutdown()
        return self.cluster_info

    def uninstall(self):
        if self.ray_cluster is not None:
            # TODO: maybe we can use uniscale(head_addr="").shutdown() instead.
            self.ray_cluster.shutdown()
        else:
            uniscale.shutdown()

    def other_ops(self):
        pass


if __name__ == "__main__":
    env_file = "default.yaml"
    ins = UniscaleCluster(env_file)
    ins.install()
    ins.uninstall()

    # ins = UniscaleCluster()
    # ins.install()
    # ins.uninstall()
