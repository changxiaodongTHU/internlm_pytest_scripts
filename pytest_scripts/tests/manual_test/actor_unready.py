import time

import ray


def actor_unready():
    @ray.remote
    def sleep():
        time.sleep(999)

    @ray.remote(num_cpus=2)
    class Actor:
        def __init__(self, x):
            pass

    # actor without name
    # a = Actor.remote(sleep.remote())
    # actor with name
    Actor.options(name="testk1223", lifetime="detached").remote(sleep.remote())
    time.sleep(180)


if __name__ == "__main__":
    ray.init(address="ray://10.140.0.73:10001", namespace="testk1223")
    actor_unready()
