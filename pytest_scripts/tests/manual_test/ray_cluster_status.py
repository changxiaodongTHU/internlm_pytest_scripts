import time

import requests


def get_nodes_ip(result, record_csv):
    for i in range(len(result["data"]["clients"])):
        if "ip" in result["data"]["clients"][i].keys():
            node = result["data"]["clients"][i]
            # print(node["mem"],node["diskIo"],node["networkSpeed"])
            with open(record_csv, "a") as f:
                f.write(
                    node["ip"]
                    + ","
                    + str(int(node["now"] * 1000))
                    + ","
                    + str(node["cpu"])
                    + ","
                    + str(node["mem"][0])
                    + ","
                    + str(node["mem"][1])
                    + ","
                    + str(node["mem"][2])
                    + ","
                    + str(node["mem"][3])
                    + ","
                    + str(node["diskIo"][0])
                    + ","
                    + str(node["diskIo"][1])
                    + ","
                    + str(node["diskIo"][2])
                    + ","
                    + str(node["diskIo"][3])
                    + ","
                    + str(node["networkSpeed"][0])
                    + ","
                    + str(node["networkSpeed"][1])
                    + "\n"
                )


if __name__ == "__main__":

    begin_time = int(time.time() * 1000)
    record_csv = "./node_status_" + str(begin_time) + ".csv"
    print(f"see metrics in {record_csv}")
    with open(record_csv, "a") as f:
        f.write(
            "ip"
            + ","
            + "time"
            + ","
            + "cpu"
            + ","
            + "mem_0"
            + ","
            + "mem_1"
            + ","
            + "mem_2"
            + ","
            + "mem_3"
            + ","
            + "diskIo_0"
            + ","
            + "diskIo_1"
            + ","
            + "diskIo_2"
            + ","
            + "diskIo_3"
            + ","
            + "networkSpeed_0"
            + ","
            + "networkSpeed_1"
            + "\n"
        )
    # while True:
    for i in range(380):
        url = "http://10.140.1.176:8265/nodes?view=details"
        result = requests.get(url)
        result = result.json()
        get_nodes_ip(result, record_csv)
        time.sleep(10)
