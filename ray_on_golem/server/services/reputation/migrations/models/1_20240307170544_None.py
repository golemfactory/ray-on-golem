from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "node" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "node_id" VARCHAR(42) NOT NULL UNIQUE,
    "name" TEXT NOT NULL
) /* Single Golem node record. */;
CREATE TABLE IF NOT EXISTS "nodereputation" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "success_rate" REAL NOT NULL,
    "uptime" REAL NOT NULL,
    "node_id_id" INT NOT NULL REFERENCES "node" ("id") ON DELETE CASCADE
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
