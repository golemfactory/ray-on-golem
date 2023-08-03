from aiohttp import web

from golem_ray.server.consts.urls import GolemRayURLs
from golem_ray.server.models.models import SingleNodeRequestData, CreateClusterRequestData, \
    NonTerminatedNodesRequestData, CreateNodesRequestData, DeleteNodesRequestData, SetNodeTagsRequestData, \
    CreateNodesResponseData, GetNodesResponseData, IsRunningResponseData, IsTerminatedResponseData, \
    GetNodeTagsResponseData, GetNodeIpAddressResponseData
from golem_ray.server.services.ray import RayService

routes = web.RouteTableDef()

golem_clusters = {}


@routes.post(GolemRayURLs.CREATE_CLUSTER)
async def create_demand(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    provider_config = CreateClusterRequestData.parse_raw(await request.text())
    await ray_service.create_cluster_on_golem(provider_config=provider_config)
    response = GetNodesResponseData(nodes=ray_service.get_all_nodes_ids())

    return web.Response(text=response.json()) 


@routes.post(GolemRayURLs.GET_NODES)
async def non_terminated_nodes_ids(request):
    ray_service: RayService = request.app['ray']
    request_data = NonTerminatedNodesRequestData.parse_raw(await request.text())
    response = GetNodesResponseData(nodes=ray_service.get_non_terminated_nodes_ids(tags_to_match=request_data.tags))

    return web.Response(text=response.json())


@routes.post(GolemRayURLs.IS_RUNNING)
async def is_node_running(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = SingleNodeRequestData.parse_raw(await request.text())
    response = IsRunningResponseData(is_terminated=ray_service.is_node_running(request_data.node_id))

    return web.Response(text=response.json())


@routes.post(GolemRayURLs.IS_TERMINATED)
async def is_node_terminated(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = SingleNodeRequestData.parse_raw(await request.text())
    response = IsTerminatedResponseData(is_terminated=ray_service.is_node_terminated(request_data.node_id))

    return web.Response(text=response.json())


@routes.post(GolemRayURLs.NODE_TAGS)
async def get_node_tags(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = SingleNodeRequestData.parse_raw(await request.text())
    response = GetNodeTagsResponseData(tags=ray_service.get_node_tags(request_data.node_id))

    return web.Response(text=response.json())


@routes.post(GolemRayURLs.INTERNAL_IP)
async def get_node_internal_ip(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = SingleNodeRequestData.parse_raw(await request.text())
    response = GetNodeIpAddressResponseData(ip_address=ray_service.get_node_internal_ip(request_data.node_id))

    return web.Response(text=response.json())


@routes.post(GolemRayURLs.SET_NODE_TAGS)
async def set_node_tags(request):
    ray_service: RayService = request.app['ray']
    request_data = SetNodeTagsRequestData.parse_raw(await request.text())
    ray_service.set_node_tags(node_id=request_data.node_id,
                              tags=request_data.tags)

    return web.Response()


@routes.post(GolemRayURLs.CREATE_NODES)
async def create_nodes(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = CreateNodesRequestData.parse_raw(await request.text())
    await ray_service.create_nodes(request_data.count, request_data.tags)
    response = CreateNodesResponseData(nodes=ray_service.get_all_nodes_dict())

    return web.Response(text=response.json())


@routes.post(GolemRayURLs.TERMINATE_NODES)
async def terminate_nodes(request):
    ray_service: RayService = request.app['ray']
    request_data = DeleteNodesRequestData.parse_raw(await request.text())
    await ray_service.terminate_nodes(request_data.node_ids)
    response = GetNodesResponseData(nodes=ray_service.get_all_nodes_ids())

    return web.Response(text=response.json())
