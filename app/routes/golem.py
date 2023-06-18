from aiohttp import web
from aiohttp_session import get_session
from app.views.golem import GolemNodeProvider

routes = web.RouteTableDef()

golem_clusters = {}


@routes.post('/create_cluster')
async def create_cluster(request: web.BaseRequest):
    json_decoded = request.json()
    image_hash = json_decoded.__getattribute__('image_hash')
    golem_node = GolemNodeProvider(image_hash)
    await golem_node.create_cluster()
    golem_clusters[len(golem_clusters) - 1] = golem_node
    return web.Response()


@routes.get('/node')
async def get_node(request):
    pass


@routes.post('/node')
async def add_nodes(request):
    json_decoded = request.json()
    session = await get_session(request)
    golem_node: GolemNodeProvider = session['golem_node']
    count: int = json_decoded.__getattribute__('count')
    await golem_node.start_workers(count)

    pass


@routes.delete('/node/{node_id}')
async def delete_node(request):
    session = await get_session(request)
    node_id = request.match_info['node_id']
    pass
