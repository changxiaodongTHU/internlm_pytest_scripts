import re


def parse_log_get_metrics(log_file_path):
    flag = False
    with open(log_file_path, 'r') as f:
        parse_log_dict_list = []
        tflops_list = []
        tgs_list = []
        for line in f:
            ll = line.strip()
            if (not flag) and re.match("[0-9]{4}-[0-9]{2}-[0-9]{2}", ll):
                time_str = ll.split(",")[0]
                flag = True
            if "internlm_" in ll:
                case_name = "internlm_" + ll.split("internlm_")[1].split(" ")[0][:-3]
            metrics_dict = dict()
            if "tflops=" in ll:
                label_result = "tflops=" + ll.split("tflops=")[1]
                label_result_list = label_result.split(",")
                for item in label_result_list:
                    key = item.split("=")[0]
                    value = float(item.split("=")[1])
                    if key == "tflops":
                        tflops_list.append(value)
                    if key == "tgs (tokens/gpu/second)":
                        tgs_list.append(value)
                    metrics_dict[key] = value
                parse_log_dict_list.append(metrics_dict)

        sorted(tflops_list)
        sorted(tgs_list)

        test_result = dict()
        test_result["case_name"] = case_name
        test_result["tflops_min"] = tflops_list[0]
        test_result["tflops_max"] = tflops_list[-1]
        test_result["tflops_avg"] = sum(tflops_list[1:-1]) / len(tflops_list[1:-1])
        test_result["tgs_min"] = tgs_list[0]
        test_result["tgs_max"] = tgs_list[-1]
        test_result["tgs_avg"] = sum(tgs_list[1:-1]) / len(tgs_list[1:-1])
        test_result["run_time"] = time_str

        return test_result
