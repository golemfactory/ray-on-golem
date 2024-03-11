from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "network" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "network_name" VARCHAR(32) NOT NULL UNIQUE
) /* The network (blockchain) that the nodes operate on. */;
CREATE TABLE IF NOT EXISTS "node" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "node_id" VARCHAR(42) NOT NULL UNIQUE,
    "name" TEXT NOT NULL
) /* Single Golem node record. */;
CREATE TABLE IF NOT EXISTS "nodereputation" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "success_rate" REAL NOT NULL,
    "uptime" REAL NOT NULL,
    "blacklisted_until" TIMESTAMP NOT NULL  DEFAULT '1970-01-01T00:00:00+00:00',
    "network_id" INT NOT NULL REFERENCES "network" ("id") ON DELETE CASCADE,
    "node_id" INT NOT NULL REFERENCES "node" ("id") ON DELETE CASCADE
) /* Reputation scores for Golem nodes. */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
