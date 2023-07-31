# Test Config Format

> Define test config format input to test framework

**Take OpenMMLab performance test as an example**

```yaml
metadata:
  cluster_num: '2'
  default_floating_range: 0.5
  model_floating_ranges: {}
  partition: mm_det
  repo: mmdetection
  task_type: openmmlab_benchmark_test
  third_part_libs: []
cases:
- name: yolof_r50-c5_8xb8-1x_coco
  params:
    checkpoint: yolof_r50_c5_8x8_1x_coco_20210425_024427-8e864411.pth
    checkpoint_url: https://download.openmmlab.com/mmdetection/v2.0/yolof/yolof_r50_c5_8x8_1x_coco/yolof_r50_c5_8x8_1x_coco_20210425_024427-8e864411.pth
    config: configs/yolof/yolof_r50-c5_8xb8-1x_coco.py
    cpus_per_node: 4
    gpus: 8
    gpus_per_node: 8
    results:
      dataset: coco
      eval:
        - bbox
      metrics:
        coco/bbox_mAP: 37.5
- name: yolox_s_8xb8-300e_coco
  params:
    checkpoint: yolox_s_8x8_300e_coco_20211121_095711-4592a793.pth
    checkpoint_url: https://download.openmmlab.com/mmdetection/v2.0/yolox/yolox_s_8x8_300e_coco/yolox_s_8x8_300e_coco_20211121_095711-4592a793.pth
    config: configs/yolox/yolox_s_8xb8-300e_coco.py
    cpus_per_node: 4
    gpus: 8
    gpus_per_node: 8
    results:
      dataset: coco
      eval:
        - bbox
      metrics:
        coco/bbox_mAP: 40.5
```

> PS: Only "metadata" and "cases" are necessary 