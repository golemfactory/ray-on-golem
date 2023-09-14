from datetime import datetime

DEAL_COUNT = 50

import ray

# endplay library dependency
runtime_env = {"pip": ["endplay==0.4.11b0"]}

# Use default ray cluster or start a local one
# Make sure endplay lib is installed
ray.init(runtime_env=runtime_env)

print(
    """This cluster consists of
          {} nodes in total
          {} CPU resources in total
      """.format(
        len(ray.nodes()), ray.cluster_resources()["CPU"]
    )
)


@ray.remote
def get_deal():
    from endplay.dds import calc_dd_table
    from endplay.dealer import generate_deal

    d = generate_deal()
    table = calc_dd_table(d)

    return str(d) + " " + str(table)


def get_lots_of_deals():
    result_ids = [get_deal.remote() for i in range(DEAL_COUNT)]

    results = ray.get(result_ids)

    return results


start = datetime.now()

results = get_lots_of_deals()
print(results)

print(
    """This cluster consists of
          {} nodes in total
          {} CPU resources in total
      """.format(
        len(ray.nodes()), ray.cluster_resources()["CPU"]
    )
)

print("[WITH RAY] deal count:", len(results), "time:", datetime.now() - start)
