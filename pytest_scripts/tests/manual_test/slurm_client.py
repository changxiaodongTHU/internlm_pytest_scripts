import pyslurm


class Slurm:
    # S/S1/S2 cluster not supported
    def __init__(self, cluster_addr):
        self.cluster_addr = cluster_addr

    def scancel(self, job_id):
        pyslurm.slurm_kill_job(job_id)

    def sbatch(self, job_params, wait_finished=True):
        job_id = pyslurm.job().submit_batch_job(job_params)
        # start_job_state = pyslurm.job().find_id(job_id)[0]["job_state"]
        if wait_finished is True:
            exit_code = pyslurm.job().wait_finished(job_id)
            if exit_code == 0:
                return job_id
            else:
                return False
        else:
            return job_id

    def skill(self, job_id):
        return pyslurm.slurm_kill_job(job_id)
