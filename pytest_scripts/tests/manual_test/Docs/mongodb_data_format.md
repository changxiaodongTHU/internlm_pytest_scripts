# MongoDB Data Format

> Define test result format uploaded to MongoDB

**Take OpenMMLab performance test as an example**

```json
{
  "metadata": {
    "type": "slurm",
    "job_id": 839021,
    "job_name": "helloworld",
    "start_time": 378219321037212,
    "run_time": 398103712738901,
    "srun_status": "CD",
    "partition": "mm_det",
    "exclusive": false,
    "node_list": "SH-IDC1-10-140-1-[60-61,83-84,89-91,93]",
    "log_path": "/mnt/petrelfs/lijialun/.log/phoenix-slurm-1072232.out",
    "resources": {
      "gpu": 64,
      "cpu": 128
    }
  },
  "test_result": {
    "repo": "mmdetection",
    "branch": "dev-3.x",
    "case": "autoassign_r50-caffe_fpn_1x_coco",
    "config": "configs/autoassign/autoassign_r50-caffe_fpn_1x_coco.py",
    "test_version": "demo",
    "success": true,
    "results": {
      "dataset": "coco",
      "eval": [
        "bbox"
      ],
      "metrics": {
        "coco/bbox_mAP": "0.4040"
      },
      "baseline": {
        "coco/bbox_mAP": "40.5"
      }
    }
  }
}
```
