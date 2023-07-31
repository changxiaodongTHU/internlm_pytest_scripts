import datetime
import os
import sys

from mnist.mnist_pytorch import train_per_epoch

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


if __name__ == "__main__":
    import uniscale

    print(f"{datetime.datetime.now()},begin init")
    # ray job submit way
    uniscale.init(gcs_address="10.140.0.242:6379")
    # client way
    # uniscale.init("10.140.0.242:10001")

    # Single actor to run a function
    train_func = train_per_epoch
    train_kwargs = {
        "epochs": 2,
        "lr": 1.0,
        "gamma": 0.7,
        "network_name": "ResNet18",
        "use_gpu": True,
    }
    resource_per_work = uniscale.Resource(num_cpus=3, num_gpus=1)

    ddp_path = uniscale.TorchDDPPath(
        name="TorchDDPPathExample",
        worker_num=1,
        resource_per_work=resource_per_work,
        dist_backend="nccl",
        train_func=train_func,
        train_kwargs=train_kwargs,
    )
    assert ddp_path.status == uniscale.PathStatus.UNSUBMITTED
    uniscale.submit_path(ddp_path)
    path_result = ddp_path.get_result()
    assert ddp_path.status == uniscale.PathStatus.COMPLETED
    assert not issubclass(type(path_result), BaseException)
    print(path_result)
    print(ddp_path.status)
    print(ddp_path.uuid)
    assert path_result[0] > 0.95

    # Must be called after using the submit_path() function
    uniscale.delete_path(ddp_path)

    uniscale.shutdown()
