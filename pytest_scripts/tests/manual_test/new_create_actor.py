import argparse
import os
import sys
import time
from threading import Thread

import requests
import torch
from examples.mnist.mnist_pytorch import train_per_epoch

import uniscale

parser = argparse.ArgumentParser(description="Create many actors parallel")
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def actor_action(node_ip, i, specify_type):
    # define the actor of actions in head node or compute node without gpu
    a = 0
    while True:
        tensor_one = torch.randn(300, 224)
        tensor_two = torch.randn(224, 400)
        mat_result = torch.matmul(tensor_one, tensor_two)
        torch.save(mat_result, "./new_tensor_test.pt")
        # cpu_load = torch.load("./simple.pt", map_location=torch.device('cpu'))
        # print(cpu_load)
        # send request
        url = "http://%s:8265/api/cluster_status" % (node_ip)
        print(url)
        result = requests.get(url)
        with open("./stats_all.txt", "a") as f:
            f.write(" ray cluster statsus is :\n" + str(result.json()) + "\n")
        a += 1
        print(f"{specify_type}:the {i} actor in actor_action run {a} times")
        time.sleep(30)
    return a


def actor_gpu_action(node_ip, specify_type, num_cpu, num_gpu, j):
    # define the actor of actions in compute node with gpu
    a = 0
    while True:
        create_actor_task(specify_type, num_cpu, num_gpu, j)

        # send request
        url = "http://%s:8265/api/cluster_status" % (node_ip)
        result = requests.get(url)
        with open("./stats_all.txt", "a") as f:
            f.write(" ray cluster statsus is :\n" + str(result.json()) + "\n")
        a += 1
        print(f"{specify_type}:the {j} actor in actor_gpu_action run {a} times")
        time.sleep(30)
    return a


def create_actor(specify_type, num_cpu, num_gpu, actor_num, node_ip, j):
    # node_type=uniscale.NodeType.HEAD,uniscale.NodeType.COMPUTE
    for i in range(actor_num):
        actor_name = str(specify_type) + "_thread_" + str(j) + "_" + str(i) + "_" + str(int(time.time() * 1000))
        resource = uniscale.Resource(num_cpus=num_cpu, num_gpus=num_gpu, node_type=specify_type)
        actor = uniscale.new_named_actor(name=actor_name, resource=resource)
        actor.wait()
        obj_ref = uniscale.get_named_actor(actor_name).run(actor_action, node_ip, i, specify_type)
        time.sleep(5)
        print(obj_ref)


def create_actor_task(specify_type, num_cpu, num_gpu, j):
    actor_name = "train_mnist_test_task_actor_thread_" + str(j) + "_" + str(int(time.time() * 1000))
    resource_per_work = uniscale.Resource(num_cpus=num_cpu, num_gpus=num_gpu, node_type=specify_type)
    train_func = train_per_epoch
    train_kwargs = {
        "epochs": 2,
        "lr": 1.0,
        "gamma": 0.7,
        "network_name": "ResNet18",
        "use_gpu": True,
    }

    ddp_path = uniscale.TorchDDPPath(
        name=actor_name,
        worker_num=1,
        resource_per_work=resource_per_work,
        dist_backend="nccl",
        train_func=train_func,
        train_kwargs=train_kwargs,
    )
    uniscale.submit_path(ddp_path)
    path_result = ddp_path.get_result()
    print(path_result)
    print(ddp_path.status)
    print(ddp_path.uuid)

    uniscale.delete_path(ddp_path)


def create_actor_many(specify_type, num_cpu, num_gpu, actor_num, j):
    for i in range(actor_num):
        actor_name = str(specify_type) + "_thread_" + str(j) + "_" + str(i) + "_" + str(int(time.time() * 1000))
        resource = uniscale.Resource(num_cpus=num_cpu, num_gpus=num_gpu, node_type=specify_type)
        actor = uniscale.new_named_actor(name=actor_name, resource=resource)
        time.sleep(3)
        print(actor)
        uniscale.delete_named_actor(actor_name)


if __name__ == "__main__":
    parser.add_argument("--head_node", type=str, help="head node address  for ray cluster, e.g. 10.140.0.73")
    parser.add_argument(
        "--actor_type",
        type=int,
        default=None,
        help="specify actor run model,0: head node; 1: compute node with gpu;2:compute node without gpu",
    )
    args = parser.parse_args()
    uniscale.init("%s:10001" % (args.head_node))
    if args.actor_type is None:
        for j in range(10):
            t = Thread(target=create_actor, args=(uniscale.NodeType.HEAD, 1, 0, 9, args.head_node, j))
            t.start()
        for j in range(13):
            t = Thread(target=create_actor, args=(uniscale.NodeType.COMPUTE, 1, 0, 7, args.head_node, j))
            t.start()
        for j in range(8):
            t = Thread(target=actor_gpu_action, args=(args.head_node, uniscale.NodeType.COMPUTE, 1, 1, j))
            t.start()
    elif args.actor_type == 0:
        for j in range(10):
            t = Thread(target=create_actor, args=(uniscale.NodeType.HEAD, 1, 0, 9, args.head_node, j))
            t.start()
    elif args.actor_type == 1:
        for j in range(8):
            t = Thread(target=actor_gpu_action, args=(args.head_node, uniscale.NodeType.COMPUTE, 1, 1, j))
            t.start()
    elif args.actor_type == 2:
        for j in range(13):
            t = Thread(target=create_actor, args=(uniscale.NodeType.COMPUTE, 1, 0, 7, args.head_node, j))
            t.start()
    elif args.actor_type == 3:
        for j in range(1):
            t = Thread(target=create_actor_many, args=(uniscale.NodeType.COMPUTE, 1, 0, 2, j))
            t.start()
    else:
        print("unsupported number")
    time.sleep(3600)
