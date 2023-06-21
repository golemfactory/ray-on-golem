import asyncio

from aiohttp import web
from aiohttp_session import get_session

from app.views.golem import GolemNodeProvider

routes = web.RouteTableDef()

golem_clusters = {}


def get_node_response(nodes: dict) -> dict:
    result = {
        "nodes": [
            {"id": key, **{k: v for k, v in value.items() if k != 'activity'}}
            for key, value in nodes.items()
        ]
    }
    return result


@routes.post('/create_cluster')
async def create_demand(request: web.Request) -> web.Response:
    golem: GolemNodeProvider = request.app['golem']
    provider_config = await request.json()
    nodes = await golem.create_demand(provider_config=provider_config)
    response = get_node_response(nodes)

    return web.json_response(response)


@routes.get('/nodes')
async def get_nodes(request):
    golem: GolemNodeProvider = request.app['golem']
    response = get_node_response(golem.nodes)

    return web.json_response(response)


@routes.post('/nodes')
async def add_nodes(request: web.Request) -> web.Response:
    golem: GolemNodeProvider = request.app['golem']
    json_decoded = await request.json()
    count: int = json_decoded.get('count')

    nodes = await golem.start_workers(count)
    response = get_node_response(nodes)

    return web.json_response(response)


@routes.delete('/node/{node_id}')
async def delete_node(request):
    # TODO: Finish endpoint
    session = await get_session(request)
    node_id = request.match_info['node_id']
    pass
