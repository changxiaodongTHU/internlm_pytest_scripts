# how to use the script: SRUN_ARGS="-x SH-IDC1-10-140-0-167" sh examples/launch_b1_debug.sh 10.140.0.228:10001

SRUN_ARGS=${SRUN_ARGS:-""}
SERVER_ADDRESS=$1
GCS_ADDRESS=$2
START_TIME=$3
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

ray job submit \
      --address=http://${SERVER_ADDRESS} \
      --job-id=b21_s1 \
      --working-dir="./" -- \
      python main.py \
      BENCHMARK2_1 \
      --experiment-name uniscale_b21_S1 \
      --skip-intermediate-state-secs 60 \
      --generation_size 4 \
      --gcs_address ${GCS_ADDRESS} \
      --ddp_num_worker 1 \
      --log-dir $logger_dir \
      --experiments-root-dir "/mnt/petrelfs/share_data/$USER/mu2net_ckpts/" \
      2>&1 | tee -a $LOG_FILE
