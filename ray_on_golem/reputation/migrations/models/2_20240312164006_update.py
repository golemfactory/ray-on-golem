from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE UNIQUE INDEX "uid_nodereputat_node_id_bde6e1" on "nodereputation"("node_id", "network_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "uid_nodereputat_node_id_bde6e1";"""
