import argparse
import copy
import json
import math
import os
import sys
import time
from collections import defaultdict

import mu2net.utils
from ml_collections import FrozenConfigDict
from mu2net.amp_utils import TF32Switch
from mu2net.dataset import ds_clean, ds_preload
from mu2net.exp_config import (
    BenchmarkMap,
    get_config_info,
    get_lr_mutate_range,
    get_num_task_iters,
    setup_exp,
)
from mu2net.mutation import (
    Path,
    Population,
    df_leaderboard,
    pop_to_df,
    save_exp_config,
    save_state,
)
from mu2net.train import run_all_test_evals, train_loop
from mu2net.utils import get_env_debug_flag, get_logger, reproduce_randomness

import uniscale

if "--log-dir" in sys.argv:
    log_dir_index = sys.argv.index("--log-dir")  # find --log-dir option
    logger = get_logger("main", log_dir=sys.argv[log_dir_index + 1])
else:
    logger = get_logger("main")


config_parser = parser = argparse.ArgumentParser(description="Training Config", add_help=False)

parser = argparse.ArgumentParser(description="UniScale Mu2Net Training")
parser.add_argument("--server_address", default=None, help="server_address to start uniscale")
parser.add_argument("--gcs_address", default=None, help="gcs_address to start uniscale,example:10.140.0.75:6379")
parser.add_argument(
    "benchmark",
    type=lambda benchmark: BenchmarkMap[benchmark],
    choices=list(BenchmarkMap),
    default="TEST",
    help="benchmark NAME",
)
parser.add_argument("--experiment-name", default="UniScale-Mu2Net ", help="Experiment NAME")
parser.add_argument(
    "--configuration",
    default="muNet",
    help="the config to run the μ2Net evolutionary method",
)
parser.add_argument("--auto-tune", action="store_true", default=True, help="auto tune")
parser.add_argument("--continue-from-state-dir", default="", help="continue from state dir")
parser.add_argument("--experiments-root-dir", default="/tmp/", help="experiment root dir")
parser.add_argument("--log-dir", default="/tmp/", help="log file dir")
parser.add_argument(
    "--auto_continue",
    action="store_true",
    default=False,
    help="auto resume training from latest checkpoint",
)
parser.add_argument(
    "--skip-intermediate-state-secs",
    default=3600,
    type=int,
    help="Skip intermediate state save if last state was written within this time range",
)
parser.add_argument("--generation_size", default=1, type=int, help="generation_size used to train")
parser.add_argument(
    "--ddp_num_worker",
    default=1,
    type=int,
    help="num of process use to train a single DDP model",
)
parser.add_argument(
    "--switched_ddp_num",
    default=1,
    type=int,
    help="num of process use to train a single DDP model aftering switching",
)
parser.add_argument(
    "--no_incremental_ckpts",
    action="store_true",
    default=False,
    help="save all components instead of only saving the components that are updated or generated in current task loop",
)

timings = {}
SKIP_INTERMEDIATE_STATE_SECS = 3600


def task_iter(
    task,
    generation_size,
    pop: Population,
    generation_id: int,
    loop_id: int,
    exp_config: FrozenConfigDict,
    args,
):
    logger.info("Start task_iter")

    tf32_switch = TF32Switch(exp_config.get("use_tf32", None))

    # Track the best path.
    best_path = pop.get_best_path(task)
    global timings  # pylint:disable=W0602
    timing_matrix = {}
    write_threads = []
    num_gen_batches = math.ceil(
        get_config_info(exp_config, loop_id, config_key="num_samples_per_task") / generation_size
    )
    for _ in range(num_gen_batches):
        logger.info(f"mu2net.utils.LAST_CHECKPOINT_TIME {mu2net.utils.LAST_CHECKPOINT_TIME}")
        cur_generation_timing = {}
        # normal case
        if generation_id + 1 > num_gen_batches:
            break
        # use acc threshold case
        if exp_config.get("use_acc_threshold", False) and generation_id + 1 > exp_config.max_gen_num:
            logger.info(f"Max generation number {exp_config.max_gen_num} is reached")
            break
        print("----")
        print(f"GENERATION: [{generation_id + 1}/{num_gen_batches}]")
        logger.info("----")
        logger.info(f"GENERATION: [{generation_id + 1}/{num_gen_batches}]")
        sample_beg = time.time()
        ds_hparams = pop.sample_ds_hparams(task)
        paths = []
        world_size = generation_size
        logger.info(f"population parameter num before path sampling:{pop.get_num_parameters()}")
        for child_index in range(world_size):
            child_path = pop.sample_path(task, ds_hparams, loop_id, generation_id, child_index, exp_config)
            paths.append(child_path)
            # record the return info after train loop to update the population
        path_hash_map = {}
        if get_env_debug_flag() >= 5:
            for i in range(len(paths)):
                path_hash_map[paths[i].id] = copy.deepcopy(paths[i].get_hash())
        logger.info(f"population parameter num after path sampling:{pop.get_num_parameters()}")
        logger.info(f"TIMECOST-sample_path: {time.time() - sample_beg:.0f}")
        cur_generation_timing["sample_path"] = round(time.time() - sample_beg)

        # ============== train_loop block begin, do not insert code ==========================
        train_infos = dict(loop_id=loop_id, gen_id=generation_id, client_call_time=time.time())
        logger.info("Start train_loop ")
        train_beg = time.time()
        # train loop
        # record the return info for each path after training.
        paths_return_info = train_loop(paths, task, ds_hparams, exp_config, train_infos)
        cur_generation_timing["train_loop"] = round(time.time() - train_beg)
        logger.info(f"TIMECOST-train_loop: {time.time() - train_beg:.0f}")
        logger.info("End train_loop, update components ... ")
        # ============== train_loop block end, do not insert code ============================

        update_beg = time.time()
        # update each path's trainable components.
        cur_generation_timing["train_actor_info"] = []
        path_ids_add_to_pop = []
        cur_generation_timing["actor_return_to_main"] = []
        time_sc = 0.0
        for i in range(world_size):
            # the trainable components of improved path will be updated
            # and be appended to pop.
            path_return_info = paths_return_info[i][0]
            actor_timing_info = paths_return_info[i][1]
            cur_generation_timing["actor_return_to_main"].append(time.time() - actor_timing_info["actor_end_time"])
            cur_generation_timing["train_actor_info"].append(actor_timing_info)

            if get_env_debug_flag() >= 5:
                # if metrics == -1, path component params should not changed after train_loop
                if path_return_info["metrics"] == -1:
                    assert (
                        path_hash_map[paths[i].id] == paths[i].get_hash()
                    ), "path component params are modified, but they should not change"
            if path_return_info["metrics"] != -1:
                for k, v in path_return_info["trainable_components"].items():
                    paths[i].symbol_components[int(k)] = v
                paths[i].metrics = path_return_info["metrics"]
                assert paths[i] not in pop.paths
                if get_env_debug_flag() >= 5:
                    # if metrics != -1, path component params should have changed after train_loop
                    if not path_hash_map[paths[i].id] != paths[i].get_hash():
                        print("path {paths[i].id} component params should be changed, but they did not change")
                # the updated path will be appended into pop.
                logger.info(f"before add new path:{paths[i].id}, population param num:{pop.get_num_parameters()}")
                pop.paths[task].append(paths[i])
                path_ids_add_to_pop.append(paths[i].id)
                # if debug mode is on, add the path status info to dict.
                if get_env_debug_flag() >= 5:
                    mu2net.utils.add_path_status_info(task, paths[i])
                logger.info(f"after add new path:{paths[i].id}, population param num:{pop.get_num_parameters()}")
                paths[i].logger.info(
                    f"Append child path: {paths[i].id} into population"
                )  # this log will be write into child model log file
            else:
                num_sc_deleted = 0
                for sc in paths[i].symbol_components:
                    if sc.is_trainable():
                        time_sc1 = time.time()
                        sc.delete()
                        time_sc += time.time() - time_sc1
                        num_sc_deleted += 1
                        logger.debug(f"symbol component {sc.name} {sc.id} is deleted from global storage.")
                logger.debug(f"{num_sc_deleted} symbol components are deleted.")

        logger.info(f"[Global Storage] task_iter: delete costs: {time_sc}s")
        logger.info(f"TIMECOST-update trainable components: {time.time() - update_beg:.0f}")
        logger.info(f"Following child paths: {path_ids_add_to_pop} have been added to population")
        df_leaderboard(pop_to_df(pop))
        cur_generation_timing["component_update"] = round(time.time() - update_beg)
        timing_matrix[f"gen_{generation_id + 1}"] = cur_generation_timing
        # Track the best path.
        curr_best_path = pop.get_best_path(task)
        if curr_best_path != best_path:
            if best_path:
                assert curr_best_path.score() >= best_path.score()
            best_path = curr_best_path
            best_path.metrics["new_best"] = True
            print(
                f"Best id:{best_path.id}",
                f"score:{best_path.score():.4f}",
                f'quality:{best_path.metrics["quality"]:.4f}',
                f"gen:{generation_id}",
                f"\n{best_path.hparams}",
            )
            logger.info(
                f"Best id:{str(best_path.id)} "
                f"score:{best_path.score():.4f} "
                f'quality:{best_path.metrics["quality"]:.4f} '
                f"gen:{generation_id} "
                f"\n{best_path.hparams} "
            )
        generation_id += 1

        # write to file every test generation to avoid iterrupt
        timings[str(loop_id)].update(timing_matrix)
        timing_json_file = os.path.join(exp_config.get("log_dir", "./"), "timing.json")
        logger.info(f"Timing json dumped to: {timing_json_file}")
        with open(timing_json_file, "w", encoding="utf-8") as f:
            json.dump(timings, f, indent=4)

        if generation_id < num_gen_batches:
            # Skip intermediate state save if last state was written recently.
            if (
                args.no_incremental_ckpts
                and (time.time() - mu2net.utils.LAST_CHECKPOINT_TIME) > SKIP_INTERMEDIATE_STATE_SECS
            ):
                logger.debug("Start save_state ")
                write_threads.clear()
                write_threads = save_state(pop, generation_id, loop_id, exp_config, {})
            elif not args.no_incremental_ckpts:
                logger.info("Skip checkpointing between generations since incremental saving ckpts is on.")
            else:
                logger.info(
                    "Skip checkpointing, seconds since last save:"
                    f"{time.time() -  mu2net.utils.LAST_CHECKPOINT_TIME:.0f}",
                )
            logger.debug("End save_state ")

        # break generation cycles if following conditions are all met
        if exp_config.get("use_acc_threshold", False) and generation_id + 1 > exp_config.min_gen_num:
            if (
                best_path.score()
                >= exp_config.baseline_acc_config[str(loop_id + 1)].vali_acc_baseline - exp_config.acc_threshold
            ):
                logger.info(
                    f"Acc threshold is reached, current vali acc {best_path.score()} >= "
                    f"{exp_config.baseline_acc_config[str(loop_id + 1)].vali_acc_baseline}-{exp_config.acc_threshold}"
                    f"={exp_config.baseline_acc_config[str(loop_id + 1)].vali_acc_baseline - exp_config.acc_threshold}"
                )
                break

    tf32_switch.exit()
    logger.info("End task_iter")
    logger.info("Showing Timing Details:")


def main():
    global timings
    timings = {}
    mu2net.utils.init_loop_id()
    mu2net.utils.init_last_ckpt_time()
    if get_env_debug_flag() >= 5:
        # init the path status map for debugging
        mu2net.utils.init_path_status_info()

    logger.info("Start Exp")
    args = parser.parse_args()

    if args.benchmark.name == "TEST":
        reproduce_randomness()
    server_address = args.server_address
    gcs_address = args.gcs_address
    working_dir = os.path.dirname(__file__)
    runtime_env = {"working_dir": working_dir}
    exp_start_time = time.time()
    uniscale.init(server_address=server_address, gcs_address=gcs_address, runtime_env=runtime_env)
    print(uniscale.available_resource())
    logger.info(uniscale.available_resource())
    # init root model and append it to pop
    generation_size = args.generation_size  # num of children models of a generation
    # Skip intermediate state save if last state was written within this time range.
    global SKIP_INTERMEDIATE_STATE_SECS
    SKIP_INTERMEDIATE_STATE_SECS = args.skip_intermediate_state_secs
    logger.info("Start setup_exp")

    pop, exp_config, generation_id, mu2net.utils.loop_id = setup_exp(args)
    train_infos = dict(loop_id=0, log_dir=exp_config.get("log_dir", "/tmp"))

    timing_json_file = os.path.join(exp_config.get("log_dir", "./"), "timing.json")
    if args.auto_continue and os.path.exists(timing_json_file):
        # load timing.json from file
        logger.info(f"Load timings from {timing_json_file}")
        with open(timing_json_file, "r", encoding="utf-8") as file:
            timings = json.load(file)

    if generation_id == 0 and mu2net.utils.loop_id == 0:
        # save initial ckpt on debug, and only state_0_0, do not work for autocontinue
        logger.debug(f"saving initial ckpt: generation_id: {generation_id}, loop_id:{mu2net.utils.loop_id}")
        write_threads = save_state(pop, generation_id, mu2net.utils.loop_id, exp_config, {})
        for thread in write_threads:
            thread.join()
    if get_env_debug_flag():
        run_all_test_evals(pop, exp_config, train_infos, test_immutability=True)

    num_tasks = len(exp_config.task_names)
    num_loops = get_num_task_iters(exp_config, mu2net.utils.loop_id) * num_tasks
    # under config changing mode, generation_size may changing.
    generation_size = get_config_info(exp_config, mu2net.utils.loop_id, config_key="generation_size")
    logger.info(f"generation_size:{generation_size}, num_tasks:{num_tasks}, num_loops:{num_loops}")
    time_matrix = defaultdict(list)
    write_threads = []
    for _ in range(num_loops):
        generation_size = get_config_info(exp_config, mu2net.utils.loop_id, config_key="generation_size")
        if not timings.get(str(mu2net.utils.loop_id)):
            timings[str(mu2net.utils.loop_id)] = {}
        if mu2net.utils.loop_id >= num_loops:
            break
        task_idx = mu2net.utils.loop_id % num_tasks
        task_name = exp_config.task_names[task_idx]
        if exp_config.get("is_changing", False):
            old_config_loop_id_str = str(mu2net.utils.latest_config_loop_id)
            if str(mu2net.utils.loop_id + 1) in exp_config.switch_loop_config and mu2net.utils.loop_id + 1 > 1:
                log_str = (
                    f"config changing at loop {str(mu2net.utils.loop_id + 1)}  with task {task_name} from: \n"
                    + str(exp_config.switch_loop_config[old_config_loop_id_str])
                    + "to: \n"
                    + str(exp_config.switch_loop_config[str(mu2net.utils.loop_id + 1)])
                )
                logger.info(log_str)
                # switch lr based on ddp worker change
                curr_ddp_num = exp_config.switch_loop_config[str(mu2net.utils.loop_id + 1)].ddp_num_worker
                default_ddp_num = exp_config.switch_loop_config["1"].ddp_num_worker
                for path in pop.paths.values():
                    # before task_iter sample path, every task in pop.paths should contains only 1 path.
                    if len(path) == 1:
                        path[0].hparams["opt_lr"] = exp_config.models_default_hparams["opt_lr"] / (
                            default_ddp_num / curr_ddp_num
                        )  # change parents lr to legal value
        print("\n\n====")
        print(f"LOOP: [{mu2net.utils.loop_id + 1}/{get_num_task_iters(exp_config, mu2net.utils.loop_id) * num_tasks}]")

        logger.info(
            f"LOOP: [{mu2net.utils.loop_id + 1}/{get_num_task_iters(exp_config, mu2net.utils.loop_id) * num_tasks}]"
        )
        logger.info(f"TASK: {task_name}")

        # task will be sampled and be launched from rank0,
        # then be sent to other ranks
        task_beg = time.time()
        task = Path.tasks(task_name=task_name)

        # update num. samples on each GPU and etc.
        task.update_config(exp_config)
        # shared dataset pre-load
        if exp_config.use_datashared:
            ds_t1 = time.time()
            ds_preload(task, pop)
            ds_t2 = time.time()
            logger.debug(f"dataset preload time: {ds_t2 - ds_t1} s")

        prev_best = pop.start_task(task)
        logger.warning(f"args.benchmark: {args.benchmark}")
        ddp_num_worker = get_config_info(exp_config, mu2net.utils.loop_id, config_key="ddp_num_worker")
        logger.info(
            f"generation_size:{generation_size}, num_tasks:{num_tasks}, num_loops:{num_loops}, \
            ddp worker:{ddp_num_worker}"
        )
        logger.info(f"lr range:{str(get_lr_mutate_range(exp_config, mu2net.utils.loop_id))}")
        logger.info(f"warmup_ratio:{str(exp_config.models_mutation_ranges['opt_lr_warmup_ratio'])}")
        # task iteration
        task_iter(task, generation_size, pop, generation_id, mu2net.utils.loop_id, exp_config, args)

        logger.info(f"before end task, population param num {pop.get_num_parameters()}")
        sc_modified = pop.end_task(task, prev_best)
        if args.no_incremental_ckpts:
            sc_modified.clear()
        logger.info(f"after end task, population param num {pop.get_num_parameters()}")

        # Save state at the end of task iteration (after deleting the redundant paths),
        # but before the begin of next task iteration.
        if get_env_debug_flag() >= 5:
            logger.debug("Start save_state ")
            write_threads = save_state(pop, 100, mu2net.utils.loop_id, exp_config, sc_modified)
            logger.debug("End save_state ")

        task_time = round(time.time() - task_beg)
        logger.info(f"TIMECOST-Loop {mu2net.utils.loop_id}, task: {task_name}, task_iter time: {task_time:.0f}")

        generation_id = 0

        all_eval_beg = time.time()
        if args.benchmark.name not in ["TEST_BENCHMARK2_1"]:
            train_infos = dict(loop_id=mu2net.utils.loop_id, log_dir=exp_config.get("log_dir", "/tmp"))
            run_all_test_evals(pop, exp_config, train_infos, test_immutability=(get_env_debug_flag() >= 2))
        all_eval_end = time.time()
        logger.info(
            f" Loop {mu2net.utils.loop_id}, Task {task_name} run_all_test_evals time: {all_eval_end - all_eval_beg}"
        )
        logger.info(f" Loop {mu2net.utils.loop_id}, Task {task_name} train_test time: {all_eval_end - task_beg:.0f}")
        time_matrix[task_name].append(round(all_eval_end - task_beg))
        # shared dataset clean
        if exp_config.use_datashared:
            ds_t1 = time.time()
            ds_clean()
            ds_t2 = time.time()
            logger.debug(f"dataset clean time: {ds_t2 - ds_t1} s")

        save_beg = time.time()
        if exp_config.get("is_changing", False):
            if str(mu2net.utils.loop_id + 1) in exp_config.switch_loop_config:
                logger.info(
                    f"latest_config_loop_id changed from {mu2net.utils.latest_config_loop_id}"
                    f"to {mu2net.utils.loop_id + 1}"
                )
                mu2net.utils.latest_config_loop_id = mu2net.utils.loop_id + 1
        mu2net.utils.loop_id += 1
        write_threads = save_state(pop, generation_id, mu2net.utils.loop_id, exp_config, sc_modified)
        save_exp_config(exp_config)
        save_end = time.time()
        timings[str(mu2net.utils.loop_id - 1)].update(
            dict(
                task=task_name,
                task_time=all_eval_end - task_beg,
                test_eval_time=all_eval_end - all_eval_beg,
                save_state=save_end - save_beg,  # note, this is only BLOCKING time
            )
        )

    # Wait for last state write to complete.
    for t in write_threads:
        t.join()
    if args.benchmark.name == "TEST":
        df_leaderboard(pop_to_df(pop))
    uniscale.shutdown()
    timings["TIMECOST-Experiment"] = round(time.time() - exp_start_time)
    logger.info(f"TIMECOST-Experiment: {time.time() - exp_start_time:.0f}")
    logger.info(f"Time cost of each task: {json.dumps(time_matrix)}")
    logger.info("Experiment finish")
    # write to file every test iter to avoid iterrupt
    logger.info(f"Timing json dumped to: {timing_json_file}")
    with open(timing_json_file, "w", encoding="utf-8") as f:
        json.dump(timings, f, indent=4)


if __name__ == "__main__":
    main()
