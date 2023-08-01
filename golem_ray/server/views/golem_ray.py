import json

from aiohttp import web

from golem_ray.server.services.golem import GolemService
from golem_ray.server.services.ray import RayService
from models.validation import CreateNodesRequest, DeleteNodesRequest, \
    SetNodeTagsRequest, NonTerminatedNodesRequest, SingleNodeRequest, IsTerminatedResponse, IsRunningResponse, \
    GetNodeTagsResponse, GetNodeIpAddressResponse, CreateClusterRequest, CreateNodesResponse
from models.validation import GetNodesResponse

routes = web.RouteTableDef()

golem_clusters = {}


@routes.post('/create_cluster')
async def create_demand(request: web.Request) -> web.Response:
    golem: GolemService = request.app['golem']
    ray: RayService = request.app['ray']
    provider_config = CreateClusterRequest.parse_raw(await request.text())
    await golem.create_cluster(provider_config=provider_config)
    response = GetNodesResponse(nodes=ray.get_all_nodes_ids())

    return web.Response(text=response.json(), status=201)


@routes.post('/')
async def non_terminated_nodes_ids(request):
    ray: RayService = request.app['ray']
    request_data = NonTerminatedNodesRequest.parse_raw(await request.text())
    response = GetNodesResponse(nodes=ray.get_non_terminated_nodes_ids(tags_to_match=request_data.tags))

    return web.Response(text=response.json(), status=200)


@routes.post('/is_running')
async def is_node_running(request: web.Request) -> web.Response:
    ray: RayService = request.app['ray']
    request_data = SingleNodeRequest.parse_raw(await request.text())
    response = IsRunningResponse(is_terminated=ray.is_node_running(request_data.node_id))

    return web.Response(text=response.json(), status=200)


@routes.post('/is_terminated')
async def is_node_terminated(request: web.Request) -> web.Response:
    ray: RayService = request.app['ray']
    request_data = SingleNodeRequest.parse_raw(await request.text())
    response = IsTerminatedResponse(is_terminated=ray.is_node_terminated(request_data.node_id))

    return web.Response(text=response.json(), status=200)


@routes.post('/tags')
async def get_node_tags(request: web.Request) -> web.Response:
    ray: RayService = request.app['ray']
    request_data = SingleNodeRequest.parse_raw(await request.text())
    response = GetNodeTagsResponse(tags=ray.get_node_tags(request_data.node_id))

    return web.Response(text=response.json(), status=200)


@routes.post('/internal_ip')
async def get_node_internal_ip(request: web.Request) -> web.Response:
    ray: RayService = request.app['ray']
    request_data = SingleNodeRequest.parse_raw(await request.text())
    response = GetNodeIpAddressResponse(ip_address=ray.get_node_internal_ip(request_data.node_id))

    return web.Response(text=response.json(), status=200)


@routes.post('/set_tags')
async def set_node_tags(request):
    ray: RayService = request.app['ray']
    request_data = SetNodeTagsRequest.parse_raw(await request.text())
    ray.set_node_tags(node_id=request_data.node_id,
                      tags=request_data.tags)

    return web.Response(status=200)


@routes.post('/create_nodes')
async def create_nodes(request: web.Request) -> web.Response:
    ray: RayService = request.app['ray']
    request_data = CreateNodesRequest.parse_raw(await request.text())
    await ray.create_nodes(request_data.count, request_data.tags)
    response = CreateNodesResponse(nodes=ray.get_all_nodes_dict())

    return web.Response(text=response.json(), status=201)


@routes.post('/terminate')
async def terminate_nodes(request):
    ray: RayService = request.app['ray']
    request_data = DeleteNodesRequest.parse_raw(await request.text())
    await ray.terminate_nodes(request_data.node_ids)
    response = GetNodesResponse(nodes=ray.get_all_nodes_ids())

    return web.Response(text=response.json(), status=204)
