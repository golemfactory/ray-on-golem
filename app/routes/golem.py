import asyncio
import json

from aiohttp import web
from aiohttp_session import get_session

from app.views.golem import GolemNodeProvider
from models.encoder import NodesResponseEncoder

routes = web.RouteTableDef()

golem_clusters = {}


@routes.post('/create_cluster')
async def create_demand(request: web.Request) -> web.Response:
    golem: GolemNodeProvider = request.app['golem']
    provider_config = await request.json()
    await golem.create_demand(provider_config=provider_config)
    response = json.dumps(golem.get_nodes_response_dict(), cls=NodesResponseEncoder)

    return web.Response(body=response, content_type='application/json', status=201)


@routes.get('/nodes')
async def get_nodes(request):
    golem: GolemNodeProvider = request.app['golem']
    response = json.dumps(golem.get_nodes_response_dict(), cls=NodesResponseEncoder)

    return web.Response(body=response, content_type='application/json', status=200)


@routes.post('/nodes')
async def add_nodes(request: web.Request) -> web.Response:
    golem: GolemNodeProvider = request.app['golem']
    json_decoded = await request.json()
    count: int = json_decoded.get('count')

    await golem.start_workers(count)
    response = json.dumps(golem.get_nodes_response_dict(), cls=NodesResponseEncoder)

    return web.Response(body=response, content_type='application/json', status=201)


@routes.delete('/node/{node_id}')
async def delete_node(request):
    golem: GolemNodeProvider = request.app['golem']
    node_id = int(request.match_info['node_id'])
    await golem.stop_worker(node_id)
    response = json.dumps(golem.get_nodes_response_dict(), cls=NodesResponseEncoder)

    return web.Response(body=response, content_type='application/json', status=204)
