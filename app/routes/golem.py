import asyncio

from aiohttp import web
from aiohttp_session import get_session

from app.views.golem import GolemNodeProvider

routes = web.RouteTableDef()

golem_clusters = {}


@routes.post('/create_demand')
async def create_demand(request: web.Request) -> web.Response:
    golem: GolemNodeProvider = request.app['golem']
    provider_config = await request.json()
    activities = await golem.create_demand(provider_config=provider_config)
    return web.json_response({"activities_ips": list(activities.keys())})


@routes.get('/node')
async def get_node(request):
    pass


@routes.post('/node')
async def add_nodes(request: web.Request) -> web.Response:
    # TODO: Finish endpoint
    json_decoded = request.json()
    session = await get_session(request)
    golem_node: GolemNodeProvider = golem_clusters[session['golem_node_id']]
    count: int = json_decoded.__getattribute__('count')
    await golem_node.start_workers(count)

    return web.Response()


@routes.delete('/node/{node_id}')
async def delete_node(request):
    # TODO: Finish endpoint
    session = await get_session(request)
    node_id = request.match_info['node_id']
    pass
