from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE INDEX "nodereputation__blacklisted_until" on "nodereputation"("blacklisted_until");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "nodereputation__blacklisted_until";"""
