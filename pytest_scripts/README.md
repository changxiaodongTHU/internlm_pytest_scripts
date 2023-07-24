- [测例添加说明](#测例添加说明)
  - [全量测试](#全量测试)
  - [部分测试](#部分测试)
- [ci_pipeline.sh 脚本使用示例](#ci_pipelinesh-脚本使用示例)
## internlm 测例添加说明

相关测例添加在`ci/cases`目录中，在`imdeploy.json`中添加imdeploy相关的测例，
在`internlm.json`中添加internlm相关的测例，测例格式说明如下。

```json
"case名称": {
    "directory": "执行相关代码所在目录", 
    "testcases":     [
        "echo testcase1", // 在该list中填入测例的命令, 每个命令会被封装为一个pytest
        "echo testcase2"
    ]
}
```

以`internlm`的`7b_model`为例，


执行测例的命令为

```bash
srun -p llm2 --quotatype=spot -n 8 --ntasks-per-node=8 --gpus-per-task=1 python train.py --config ./configs/7B_sft.py
```

则在`ci/cases/internlm.json`中添加如下信息。

```json
    "internlm_function_0001": {
        "directory": "InternLM",
        "testcases": [
            "srun -p llm2 --quotatype=spot -n 8 --ntasks-per-node=8 --gpus-per-task=1 python train.py --config ./configs/7B_sft.py"
        ]
    }
```


## ci_pipeline.sh 脚本使用示例

需要在项目的根目录下执行

```bash
# 测试 ci/cases/internlm.json 中所有的测例
bash ci/ci_pipeline.sh internlm
# 测试 ci/cases/internlm.json 中指定的测例
bash ci/ci_pipeline.sh internlm case_id
```

