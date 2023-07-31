import argparse
import time

import ray
from prettytable import PrettyTable

parser = argparse.ArgumentParser(description="List Actors for Target Ray Cluster")


@ray.remote
def actors(states: list) -> list:
    actors = ray.state.actors()
    time.sleep(1)
    filtered_actors = []
    for keya, actor_value in actors.items():
        if actor_value["State"] not in states:
            continue

        filtered_actor = {}
        filtered_actor["name"] = actor_value["Name"]
        filtered_actor["state"] = actor_value["State"]
        filtered_actor["address"] = actor_value["Address"]["IPAddress"]
        filtered_actors.append(filtered_actor)

    return filtered_actors


if __name__ == "__main__":
    # parse arguments
    parser.add_argument("--address", type=str, help="server address for ray cluster, e.g. 10.140.0.168:10001")
    parser.add_argument(
        "--states",
        type=str,
        default="ALIVE",
        nargs="+",
        help="list actors with target state ALIVE, PENDING_CREATION or DEAD, default is ALIVE",
    )
    args = parser.parse_args()

    ray.init(address=f"ray://{args.address}")

    # get actors
    filtered_actors = ray.get(actors.remote(args.states))
    # print actors in table
    table = PrettyTable(field_names=["index", "actor_name", "state", "address"])
    for index, filtered_actor in enumerate(sorted(filtered_actors, key=lambda actor: actor["name"])):
        table.add_row([index, filtered_actor["name"], filtered_actor["state"], filtered_actor["address"]])

    print(table)
