from aiohttp import web

from golem_ray.server import models, settings
from golem_ray.server.services import RayService

routes = web.RouteTableDef()


@routes.get(settings.URL_HEALTH_CHECK)
async def health_check(request: web.Request) -> web.Response:
    return web.Response(text="ok")


@routes.post(settings.URL_CREATE_CLUSTER)
async def create_cluster(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.CreateClusterRequestData.parse_raw(await request.text())

    await ray_service.create_cluster_on_golem(provider_config=request_data)

    response_data = models.EmptyResponseData()

    return web.Response(text=response_data.json())


@routes.post(settings.URL_NON_TERMINATED_NODES)
async def non_terminated_nodes_ids(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.NonTerminatedNodesRequestData.parse_raw(await request.text())

    nodes_ids = await ray_service.get_non_terminated_nodes_ids(tags_to_match=request_data.tags)

    response_data = models.NonTerminatedNodesResponseData(nodes_ids=nodes_ids)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_IS_RUNNING)
async def is_node_running(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    is_running = await ray_service.is_node_running(request_data.node_id)

    response_data = models.IsRunningResponseData(is_running=is_running)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_IS_TERMINATED)
async def is_node_terminated(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    is_terminated = await ray_service.is_node_terminated(request_data.node_id)

    response_data = models.IsTerminatedResponseData(is_terminated=is_terminated)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_NODE_TAGS)
async def get_node_tags(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    node_tags = await ray_service.get_node_tags(request_data.node_id)

    response_data = models.GetNodeTagsResponseData(tags=node_tags)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_INTERNAL_IP)
async def get_node_internal_ip(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    ip_address = await ray_service.get_node_internal_ip(request_data.node_id)

    response_data = models.GetNodeIpAddressResponseData(ip_address=ip_address)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_SET_NODE_TAGS)
async def set_node_tags(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SetNodeTagsRequestData.parse_raw(await request.text())

    await ray_service.set_node_tags(
        node_id=request_data.node_id,
        tags=request_data.tags,
    )

    response_data = models.EmptyResponseData()

    return web.Response(text=response_data.json())


@routes.post(settings.URL_CREATE_NODES)
async def create_nodes(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.CreateNodesRequestData.parse_raw(await request.text())

    created_nodes = await ray_service.create_nodes(
        request_data.node_config, request_data.count, request_data.tags
    )

    response_data = models.CreateNodesResponseData(created_nodes=created_nodes)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_TERMINATE_NODE)
async def terminate_node(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    terminated_nodes = await ray_service.terminate_node(request_data.node_id)

    response_data = models.TerminateNodeResponseData(terminated_nodes=terminated_nodes)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_GET_SSH_PROXY_COMMAND)
async def get_ssh_proxy_command(request):
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    ssh_proxy_command = await ray_service.get_ssh_proxy_command(node_id=request_data.node_id)

    response_data = models.GetSshProxyCommandResponseData(ssh_proxy_command=ssh_proxy_command)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_GET_OR_CREATE_DEFAULT_SSH_KEY)
async def get_or_create_ssh_key(request):
    ray_service: RayService = request.app["ray_service"]

    request_data = models.GetOrCreateDefaultSshKeyRequestData.parse_raw(await request.text())

    ssh_key_base64 = await ray_service.get_or_create_default_ssh_key(
        cluster_name=request_data.cluster_name
    )

    response_data = models.GetOrCreateDefaultSshKeyResponseData(ssh_key_base64=ssh_key_base64)

    return web.Response(text=response_data.json())
