import asyncio

from aiohttp import web
from aiohttp_session import get_session

from app.views.golem import GolemNodeProvider

routes = web.RouteTableDef()

golem_clusters = {}


@routes.post('/create_cluster')
async def create_cluster(request: web.Request):
    json_decoded = await request.json()
    session = await get_session(request)
    image_hash = json_decoded.get('image_hash')
    golem_node_id = len(golem_clusters)
    golem_node = GolemNodeProvider(cluster_id=golem_node_id)
    await golem_node.create_cluster(image_hash=image_hash)
    # await golem_node.create_cluster()
    session['golem_node_id'] = golem_node_id
    golem_clusters[golem_node_id] = golem_node

    return web.Response(body=
                        {"golem_node_id": golem_node_id,
                         "internal_ip": golem_node.HEAD_IP})


@routes.get('/node')
async def get_node(request):
    pass


@routes.post('/node')
async def add_nodes(request: web.Request):
    json_decoded = request.json()
    session = await get_session(request)
    golem_node: GolemNodeProvider = golem_clusters[session['golem_node_id']]
    count: int = json_decoded.__getattribute__('count')
    await golem_node.start_workers(count)

    return web.Response()


@routes.delete('/node/{node_id}')
async def delete_node(request):
    session = await get_session(request)
    node_id = request.match_info['node_id']
    pass
