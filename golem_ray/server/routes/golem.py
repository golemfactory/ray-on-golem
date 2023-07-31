from aiohttp import web

from golem_ray.server.services.golem import GolemService
from golem_ray.server.services.ray import RayService
from models.validation import CreateClusterRequest, GetNodeRequest, CreateNodesRequest, DeleteNodesRequest, \
    SetNodeTagsRequest, NonTerminatedNodesRequest
from models.response import GetNodesResponse, GetNodeResponse

routes = web.RouteTableDef()

golem_clusters = {}


@routes.post('/create_cluster')
async def create_demand(request: web.Request) -> web.Response:
    golem: GolemService = request.app['golem']
    provider_config = CreateClusterRequest.parse_raw(await request.text())
    await golem.create_cluster(provider_config=provider_config)
    response = GetNodesResponse(nodes=golem.get_nodes_response())

    return web.json_response(text=response, status=201)


@routes.post('/nodes')
async def non_terminated_nodes_ids(request):
    ray: RayService = request.app['ray']
    request_data = NonTerminatedNodesRequest.parse_raw(await request.text)
    response = GetNodesResponse(nodes=ray.get_non_terminated_nodes_ids())

    return web.json_response(text=response)


@routes.get('/nodes/{node_id}')
async def get_node(request):
    golem: GolemService = request.app['golem']
    node_id = GetNodeRequest(node_id=request.match_info['node_id']).node_id
    response = GetNodeResponse(node=golem.get_node_response_by_id(int(node_id))).json()

    return web.json_response(text=response)


@routes.post('/nodes')
async def add_nodes(request: web.Request) -> web.Response:
    golem: GolemService = request.app['golem']
    request_data = CreateNodesRequest(**await request.json()).dict()
    count: int = request_data.get('count')
    tags: dict = request_data.get('tags')
    await golem.start_workers(count, tags)
    response = GetNodesResponse(nodes=golem.get_nodes_response()).json()

    return web.json_response(text=response, status=201)


@routes.post('/head_nodes')
async def add_head_nodes(request: web.Request) -> web.Response:
    golem: GolemService = request.app['golem']
    request_data = CreateNodesRequest.parse_raw(await request.text()).dict()
    await golem.start_head_process(tags=request_data['tags'])
    response = GetNodesResponse(nodes=golem.get_nodes_response()).json()

    return web.json_response(text=response, status=201)


@routes.delete('/node/{node_id}')
async def delete_node(request):
    golem: GolemService = request.app['golem']
    node_id = int(request.match_info['node_id'])
    await golem.stop_worker(node_id)
    response = GetNodesResponse(nodes=golem.get_nodes_response()).json()

    return web.json_response(text=response, status=204)


@routes.delete('/nodes')
async def delete_nodes(request):
    golem: GolemService = request.app['golem']
    request_data = DeleteNodesRequest(**await request.json()).dict()
    await golem.stop_workers_by_ids(request_data.get('node_ids'))
    response = GetNodesResponse(nodes=golem.get_nodes_response()).json()

    return web.json_response(text=response, status=204)


@routes.patch('/set_node_tags/{node_id}')
async def set_node_tags(request):
    golem: GolemService = request.app['golem']
    node_id = int(request.match_info['node_id'])
    request_data = SetNodeTagsRequest(**await request.json()).dict()
    await golem.set_node_tags(node_id=node_id,
                              tags=request_data['tags'])
    response = GetNodesResponse(nodes=golem.get_nodes_response()).json()

    return web.json_response(text=response, status=200)
