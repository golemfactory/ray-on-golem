from datetime import datetime, timezone

from tortoise import BaseDBAsyncClient

BLACKLISTED_FOREVER = datetime.fromtimestamp(2**32, tz=timezone.utc)
PROVIDERS_BLACKLIST = {
    "polygon": {
        "0xf460871f1741dd2eebfa115c3ddd8a1aaa7fa914",
        "0xc3ba6bf1464d4e10ffd3ed8e01b38524520724a0",
        "0x8842512ef4c35aba2ff2883d766c3382c50de990",
        "0xc04863f26dab1bb0d9ec35c793b01c6cc5e7a399",
        "0xfc88946eac7433315a82a0d83cef54493aa69948",
        "0xa272d86f5c0466783ecff3403786f42d18f3fc3b",
        "0x51fb0db558d9c50cae94cbbeeec4a9e55898886f",
        "0x5595546699e894cf077685a20f3ff214a217b950",
        "0x0bd56a416463d467e4e79dcf72f81b4e9ffcb924",
        "0x07cde3150460db9d148fa17360c273f1efecc258",
        "0x56c64723db51cd76eccc2098f3f05eaefd53f720",
        "0x65cffc710ff26ca593426f1669d31de84d156043",
        "0x4321552531b91f7c58b5e7d24ff083c92f8465e0",
        "0x37792f405c68a2bcee144cc9b6b5f3efabd3984d",
        "0x4bd46f8e1ed87dbfafae9293ef2aeff1fe2818a1",
        "0x1ce39f1bfb8ef5282071924a83a9b6a0359ca3c9",
        "0x1371e45b1037460b17892635e2870cfe84c4545f",
        "0x43c7383abf784186e5bc94aa22408e7768148b98",
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
