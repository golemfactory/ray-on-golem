from datetime import datetime

DEAL_COUNT = 50


def get_deal():
    from endplay.dds import calc_dd_table
    from endplay.dealer import generate_deal

    d = generate_deal()
    table = calc_dd_table(d)

    return str(d) + " " + str(table)


def get_lots_of_deals():
    results = [get_deal() for i in range(DEAL_COUNT)]

    return results


start = datetime.now()

results = get_lots_of_deals()
print(results)

print("[WITHOUT RAY] deal count:", len(results), "time:", datetime.now() - start)
