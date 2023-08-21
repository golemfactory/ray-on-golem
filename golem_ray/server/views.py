import asyncio

from aiohttp import web

import config
import models
from services import RayService

routes = web.RouteTableDef()

golem_clusters = {}

modification_lock = asyncio.Lock()


@routes.post(config.URL_CREATE_CLUSTER)
async def create_demand(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    provider_config = models.CreateClusterRequestData.parse_raw(await request.text())
    await ray_service.create_cluster_on_golem(provider_config=provider_config)
    response = models.GetNodesResponseData(nodes=ray_service.get_all_nodes_ids())

    return web.Response(text=response.json())


@routes.post(config.URL_GET_NODES)
async def non_terminated_nodes_ids(request):
    ray_service: RayService = request.app['ray']
    request_data = models.NonTerminatedNodesRequestData.parse_raw(await request.text())
    nodes = ray_service.get_non_terminated_nodes_ids(tags_to_match=request_data.tags)
    response = models.GetNodesResponseData(nodes=nodes)
    return web.Response(text=response.json())


@routes.post(config.URL_IS_RUNNING)
async def is_node_running(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = models.SingleNodeRequestData.parse_raw(await request.text())
    is_running = ray_service.is_node_running(request_data.node_id)
    response = models.IsRunningResponseData(is_running=is_running)

    return web.Response(text=response.json())


@routes.post(config.URL_IS_TERMINATED)
async def is_node_terminated(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = models.SingleNodeRequestData.parse_raw(await request.text())
    is_terminated = ray_service.is_node_terminated(request_data.node_id)
    response = models.IsTerminatedResponseData(is_terminated=is_terminated)

    return web.Response(text=response.json())


@routes.post(config.URL_NODE_TAGS)
async def get_node_tags(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = models.SingleNodeRequestData.parse_raw(await request.text())
    node_tags = ray_service.get_node_tags(request_data.node_id)
    response = models.GetNodeTagsResponseData(tags=node_tags)

    return web.Response(text=response.json())


@routes.post(config.URL_INTERNAL_IP)
async def get_node_internal_ip(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = models.SingleNodeRequestData.parse_raw(await request.text())
    ip_address = ray_service.get_node_internal_ip(request_data.node_id)
    response = models.GetNodeIpAddressResponseData(ip_address=ip_address)

    return web.Response(text=response.json())


@routes.post(config.URL_SET_NODE_TAGS)
async def set_node_tags(request):
    ray_service: RayService = request.app['ray']
    request_data = models.SetNodeTagsRequestData.parse_raw(await request.text())
    ray_service.set_node_tags(node_id=request_data.node_id,
                              tags=request_data.tags)

    return web.Response()


@routes.post(config.URL_CREATE_NODES)
async def create_nodes(request: web.Request) -> web.Response:
    ray_service: RayService = request.app['ray']
    request_data = models.CreateNodesRequestData.parse_raw(await request.text())
    await ray_service.create_nodes(request_data.count, request_data.tags)
    response = models.CreateNodesResponseData(nodes=ray_service.get_all_nodes_dict())

    return web.Response(text=response.json())


@routes.post(config.URL_TERMINATE_NODES)
async def terminate_nodes(request):
    ray_service: RayService = request.app['ray']
    request_data = models.DeleteNodesRequestData.parse_raw(await request.text())
    await ray_service.terminate_nodes(request_data.node_ids)
    response = models.GetNodesResponseData(nodes=ray_service.get_all_nodes_ids())

    return web.Response(text=response.json())


@routes.post(config.URL_GET_NODE_SSH_PORT)
async def get_node_proxy_command(request):
    ray_service: RayService = request.app['ray']
    request_data = models.SingleNodeRequestData.parse_raw(await request.text())
    port = await ray_service.get_node_ssh_port(node_id=request_data.node_id)
    response = models.GetNodePortResponseData(port=port)

    return web.Response(text=response.json())
