# how to use the script: SRUN_ARGS="-x SH-IDC1-10-140-0-167" sh examples/launch_b1_debug.sh 10.140.0.228:10001

SRUN_ARGS=${SRUN_ARGS:-""}
SERVER_ADDRESS=$1
START_TIME=$2
if [ -z "$START_TIME" ]
then
      START_TIME=`date +%Y%m%d-%H:%M:%S`
fi


logger_dir=/mnt/petrelfs/share_data/$USER/mu2net_logs/b21/$START_TIME
mkdir -p $logger_dir
# if not using your own cluster, make sure the directory can be written by others
# chmod 755 $logger_dir/actor_logs
LOG_FILE=$logger_dir/b21-s1-$START_TIME

echo "uniscale client and actor logs will be appended to $logger_dir" | tee -a $LOG_FILE


export UNISCALE_CKPT=ON

srun  -p caif_debug \
      -N 1 \
      -n 1 \
      --gres=gpu:0 \
      --cpus-per-task 5 \
      --job-name=benchmark_2_1 \
      ${SRUN_ARGS} \
      python main.py \
      BENCHMARK2_1 \
      --experiment-name uniscale_b21_S1 \
      --skip-intermediate-state-secs 60 \
      --generation_size 4 \
      --server_address ${SERVER_ADDRESS} \
      --ddp_num_worker 1 \
      --log-dir $logger_dir \
      --experiments-root-dir "/mnt/petrelfs/share_data/$USER/mu2net_ckpts/" \
      2>&1 | tee -a $LOG_FILE
