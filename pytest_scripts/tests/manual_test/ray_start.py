import re
import subprocess
import time

import requests
import yaml


class RayCluster:
    global ray_cluster
    ray_cluster = {"wait_skilled_job": []}

    def load_env(self, env_file):
        with open(env_file, "r") as f:
            params = yaml.safe_load(f)
        print(params)
        return params

    def call_command(self, command, break_condition, break_param=None, try_times=1, wait_time=1):
        for i in range(try_times):
            execute_result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = execute_result.stdout.read().decode().rstrip("\n")
            execute_result.stdout.close()
            result = re.sub("\x1b.*?m", "", result)
            exec_param = {"result_bool": False, "result": result, "param": break_param}
            exec(break_condition, exec_param)
            if exec_param["result_bool"]:
                break
            time.sleep(wait_time)
        exec_param = {"result_bool": exec_param["result_bool"], "result": exec_param["result"]}
        return exec_param

    def start_head_node(self, env_file, new_exclude=""):
        params = self.load_env(env_file)
        join_param = " "
        if params["head_node_parm"]["include"] != "":
            join_param += "-w %s " % (params["head_node_parm"]["include"])
        if params["head_node_parm"]["exclude"] != "" or new_exclude != "":
            join_param += "-x " + params["head_node_parm"]["exclude"] + "," + new_exclude
        whole_head_command = (
            "sbatch -p %s " % (params["head_node_parm"]["partition"])
            + join_param
            + " --job-name=%s --cpus-per-task=%s --gpus-per-task=%s %s"
            % (
                params["head_node_parm"]["job_name"],
                params["head_node_parm"]["cpu_per_task"],
                params["head_node_parm"]["gpu_per_task"],
                params["head_node_parm"]["script_path"],
            )
        )
        print(f"start head node command is: {whole_head_command}")
        break_condition = """import re\nresult=re.findall("\d+", result)[0]\nif result !="":\n\tresult_bool=True
        """
        get_result = self.call_command(whole_head_command, break_condition)
        get_jobid = get_result["result"]

        status_command = "squeue -j %s |awk 'NR==2 {print $7}'" % (get_jobid)
        break_condition = """if result == 'R':\n\tresult_bool=True
        """
        get_result = self.call_command(status_command, break_condition, try_times=60)

        ray_cluster["wait_skilled_job"].append(get_jobid)
        get_ip = ""
        filter_command = (
            "grep -rni 'Local node IP' slurm-%s.out |grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'"
            % (get_jobid)
        )
        break_condition = """if result != "":\n\tresult_bool=True
                """
        get_result = self.call_command(filter_command, break_condition, try_times=60)
        get_ip = get_result["result"]

        if get_ip != "":
            exclude_ip = "SH-IDC1-" + get_ip.replace(".", "-")
        else:
            exclude_ip = ""
        # check ray cluster status
        for i in range(3):
            url = "http://%s:8265/api/cluster_status" % (get_ip)
            try:
                status = requests.get(url)
                status = status.json()
            except Exception as err:
                print(err)
                if i == 2:
                    # exclude current node and start a new head node
                    subprocess.Popen(
                        "scancel %s" % (get_jobid), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    self.start_head_node(env_file, new_exclude=exclude_ip)
                time.sleep(3)
            else:
                if status["result"] is True:
                    ray_cluster["head_node"] = get_ip
                    print("head node is ready")
                    break

    def start_compute_node(self, env_file, new_exclude=""):
        params = self.load_env(env_file)
        join_param = " "
        if params["compute_node_parm"]["include"] != "":
            join_param += "-w %s " % (params["compute_node_parm"]["include"])
        if params["compute_node_parm"]["exclude"] != "" or new_exclude != "":
            join_param += "-x " + params["compute_node_parm"]["exclude"] + "," + new_exclude
        whole_compute_command = (
            "sbatch -p %s " % (params["compute_node_parm"]["partition"])
            + join_param
            + " --job-name=%s --cpus-per-task=%s --gpus-per-task=%s --nodes=%s %s -h %s"
            % (
                params["compute_node_parm"]["job_name"],
                params["compute_node_parm"]["cpu_per_task"],
                params["compute_node_parm"]["gpu_per_task"],
                params["compute_node_parm"]["nodes"],
                params["compute_node_parm"]["script_path"],
                ray_cluster["head_node"],
            )
        )
        print(f"start compute node command is: {whole_compute_command}")
        break_condition = """import re\nresult=re.findall("\d+", result)[0]\nprint(result)\nif result !="":\n\tresult_bool=True
                """
        get_result = self.call_command(whole_compute_command, break_condition, try_times=60)
        get_jobid = get_result["result"]

        status_command = "squeue -j %s |awk 'NR==2 {print $7}'" % (get_jobid)
        break_condition = """if result == 'R':\n\tresult_bool=True
                """
        get_result = self.call_command(status_command, break_condition, try_times=60)
        ray_cluster["wait_skilled_job"].append(get_jobid)

        filter_command = (
            "grep -rni 'Local node IP' slurm-%s.out |grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'"
            % (get_jobid)
        )
        break_condition = """result=result.split("\\n")\nif len(result) !=param:\n\tresult_bool=True
                        """
        get_result = self.call_command(filter_command, break_condition, params["compute_node_parm"]["nodes"], 60)

        url = "http://%s:8265/nodes?view=summary" % (ray_cluster["head_node"])
        status = requests.get(url)
        status = status.json()
        ray_live_node = []
        for i in range(len(status["data"]["summary"])):
            if status["data"]["summary"][i]["raylet"]["state"] == "ALIVE":
                if status["data"]["summary"][i]["ip"] != ray_cluster["head_node"]:
                    ray_live_node.append(status["data"]["summary"][i]["ip"])

        exclude_ip = "SH-IDC1-" + ray_cluster["head_node"].replace(".", "-") + ","
        if len(ray_live_node) < params["compute_node_parm"]["nodes"]:
            for ip in get_result["result"]:
                exclude_ip += "SH-IDC1-" + ip.replace(".", "-") + ","
            self.start_compute_node(env_file, exclude_ip)
        else:
            print("compute node is ready")
            ray_cluster["head_node"] = ray_live_node


if __name__ == "__main__":
    a = RayCluster()
    a.start_head_node("./default.yaml")
    exclude_ip = "SH-IDC1-" + ray_cluster["head_node"].replace(".", "-")
    print(exclude_ip)
    a.start_compute_node("./default.yaml", exclude_ip)
