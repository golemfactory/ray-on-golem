from datetime import datetime, timezone

from tortoise import BaseDBAsyncClient

BLACKLISTED_FOREVER = datetime.fromtimestamp(2**32, tz=timezone.utc)
PROVIDERS_BLACKLIST = {
    "polygon": {
    }
}


async def upgrade(db: BaseDBAsyncClient) -> str:
    for network in PROVIDERS_BLACKLIST.keys():
        network_id = await db.execute_insert(
            "insert into network (network_name) values(?);",
            [
                network,
            ],
        )
        for golem_node_id in PROVIDERS_BLACKLIST.get(network):
            node_id = await db.execute_insert(
                "insert into node (node_id) values(?);",
                [golem_node_id],
            )
            await db.execute_insert(
                "insert into nodereputation (network_id, node_id, blacklisted_until) values (?, ?, ?);",
                [network_id, node_id, BLACKLISTED_FOREVER],
            )

    return """
        ;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ;"""
