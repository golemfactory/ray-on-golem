import asyncio
from functools import partial
from typing import Optional

import click
from prettytable import PrettyTable
from tortoise.exceptions import DoesNotExist

from ray_on_golem.cli import with_datadir
from ray_on_golem.server.services.reputation import models as m
from ray_on_golem.server.services.reputation.service import ReputationService
from ray_on_golem.server.services.reputation.updater import ReputationUpdater


@click.group(
    name="reputation",
    help="Reputation subsystem management.",
    context_settings={"show_default": True},
)
def reputation_cli():
    ...

def with_network(cli_func=None, *, default: Optional[str] = "polygon"):

    def _with_network(_cli_func):
        return click.option(
            "--network",
            type=click.Choice(
                ["polygon", "mainnet", "goerli", "holesky"],
            ),
            default=default,
            help="The network for the score",
        )(_cli_func)

    if cli_func is None:
        return _with_network

    return _with_network(cli_func)


@reputation_cli.command(name="list", help="List reputation records.")
@click.argument(
    "node_id",
    nargs=-1,
)

@click.option(
    "--blacklist",
    is_flag=True,
    help="Show only the blacklisted nodes",
)
@with_network(default=None)
@with_datadir
def list_(datadir, network, node_id, blacklist):
    async def list_records():
        print(click.style("Node reputation{}".format(f" for network: {network}" if network else ""), fg="bright_cyan"))

        table = PrettyTable(
            ["ID", "Name", "Network", "Blacklisted?", "Success Rate", "Uptime score"]
        )

        async with ReputationService(datadir):
            if blacklist:
                qs = m.NodeReputation.get_blacklisted()
            else:
                qs = m.NodeReputation.all()

            if network:
                qs = qs.filter(network__network_name=network)

            if node_id:
                qs = qs.filter(node__node_id__in=node_id)

            async for node_reputation in qs.prefetch_related("node", "network"):
                node: m.Node = node_reputation.node
                table.add_row(
                    [
                        node.node_id,
                        node.name or "",
                        node_reputation.network.network_name,
                        node_reputation.is_blacklisted(),
                        node_reputation.success_rate
                        if node_reputation.success_rate is not None
                        else "",
                        node_reputation.uptime if node_reputation.uptime is not None else "",
                    ]
                )

        print(table)

    asyncio.run(list_records())


@reputation_cli.command(help="Add a node to blacklist.")
@click.argument(
    "node_id",
    nargs=1,
)
@with_network
@with_datadir
def block(datadir, network, node_id):
    async def _block():
        async with ReputationService(datadir):
            node, _ = await m.Node.get_or_create(node_id=node_id)
            node_network, _ = await m.Network.get_or_create(network_name=network)
            node_reputation, _ = await m.NodeReputation.get_or_create(
                node=node, network=node_network
            )
            node_reputation.blacklisted_until = m.BLACKLISTED_FOREVER
            await node_reputation.save()
            print(f"Node {node_id} blocked on {network}.")

    asyncio.run(_block())


@reputation_cli.command(help="Unblock a node.")
@click.argument(
    "node_id",
    nargs=1,
)
@with_network
@with_datadir
def unblock(datadir, network, node_id):
    async def _unblock():
        async with ReputationService(datadir):
            try:
                node_reputation = await m.NodeReputation.get(
                    node__node_id=node_id, network__network_name=network
                )
                node_reputation.blacklisted_until = m.BLACKLISTED_NEVER
                await node_reputation.save()
                print(f"Node {node_id} unblocked on {network}.")
            except DoesNotExist:
                print(f"No reputation record found for {node_id} on {network}")

    asyncio.run(_unblock())


@reputation_cli.command(help="Update local reputation data from the global Reputation System.")
@with_network
@with_datadir
def update(datadir, network):
    async def _update():
        async with ReputationService(datadir):
            cnt_added, cnt_updated, cnt_ignored, cnt_total = await ReputationUpdater(
                network
            ).update(partial(click.progressbar, label="Updating scores"))

        print(
            f"Reputation DB updated. Total scores={cnt_total} (added={cnt_added}, updated={cnt_updated}, ignored={cnt_ignored})."
        )

    asyncio.run(_update())
