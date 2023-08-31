import aiohttp
from aiohttp import web

from golem_ray.server import models, settings
from golem_ray.server.services import GolemService, RayService

routes = web.RouteTableDef()


@routes.post(settings.URL_CREATE_CLUSTER)
async def create_cluster(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.CreateClusterRequestData.parse_raw(await request.text())

    await ray_service.create_cluster_on_golem(provider_config=request_data)
    nodes = ray_service.get_all_nodes_ids()

    response_data = models.GetNodesResponseData(nodes=nodes)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_GET_NODES)
async def non_terminated_nodes_ids(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.NonTerminatedNodesRequestData.parse_raw(await request.text())

    nodes = ray_service.get_non_terminated_nodes_ids(tags_to_match=request_data.tags)

    response_data = models.GetNodesResponseData(nodes=nodes)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_IS_RUNNING)
async def is_node_running(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    is_running = ray_service.is_node_running(request_data.node_id)

    response_data = models.IsRunningResponseData(is_running=is_running)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_IS_TERMINATED)
async def is_node_terminated(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    is_terminated = ray_service.is_node_terminated(request_data.node_id)

    response_data = models.IsTerminatedResponseData(is_terminated=is_terminated)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_NODE_TAGS)
async def get_node_tags(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    node_tags = ray_service.get_node_tags(request_data.node_id)

    response_data = models.GetNodeTagsResponseData(tags=node_tags)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_INTERNAL_IP)
async def get_node_internal_ip(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    ip_address = ray_service.get_node_internal_ip(request_data.node_id)

    response_data = models.GetNodeIpAddressResponseData(ip_address=ip_address)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_SET_NODE_TAGS)
async def set_node_tags(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SetNodeTagsRequestData.parse_raw(await request.text())

    ray_service.set_node_tags(
        node_id=request_data.node_id,
        tags=request_data.tags,
    )

    response_data = models.EmptyResponseData()

    return web.Response(text=response_data.json())


@routes.post(settings.URL_CREATE_NODES)
async def create_nodes(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.CreateNodesRequestData.parse_raw(await request.text())

    await ray_service.create_nodes(request_data.count, request_data.tags)
    nodes = ray_service.get_all_nodes_dict()

    response_data = models.CreateNodesResponseData(nodes=nodes)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_TERMINATE_NODES)
async def terminate_nodes(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.DeleteNodesRequestData.parse_raw(await request.text())

    await ray_service.terminate_nodes(request_data.node_ids)
    nodes = ray_service.get_all_nodes_ids()

    response_data = models.GetNodesResponseData(nodes=nodes)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_GET_SSH_PROXY_COMMAND)
async def get_node_proxy_command(request):
    golem_service: GolemService = request.app["golem_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    ssh_proxy_command = golem_service.get_node_ssh_proxy_command(node_id=request_data.node_id)

    response_data = models.GetSshProxyCommandResponseData(ssh_proxy_command=ssh_proxy_command)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_GET_HEAD_NODE_IP)
async def get_head_node_ip(request):
    golem_service: GolemService = request.app["golem_service"]

    head_node_ip = golem_service.get_head_node_ip()

    response_data = models.GetNodeIpAddressResponseData(ip_address=head_node_ip)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_GET_IMAGE_URL_FROM_HASH)
async def get_image_url_from_hash(request):
    golem_service: GolemService = request.app["golem_service"]
    client_session: aiohttp.ClientSession = request.app["client_session"]

    request_data = models.GetImageUrlFromHashRequestData.parse_raw(await request.text())

    image_url = await golem_service.get_image_url_from_hash(
        image_hash=request_data.image_hash,
        client_session=client_session
    )

    response_data = models.GetImageUrlFromHashResponseData(url=image_url)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_GET_IMAGE_URL_AND_HASH_FROM_TAG)
async def get_image_url_and_hash_from_tag(request):
    golem_service: GolemService = request.app["golem_service"]
    client_session: aiohttp.ClientSession = request.app["client_session"]

    request_data = models.GetImageUrlAndHashFromTagRequestData.parse_raw(await request.text())

    image_url, image_hash = await golem_service.get_image_url_and_hash_from_tag(
        image_tag=request_data.image_tag,
        client_session=client_session
    )

    response_data = models.GetImageUrlAndHashFromTagResponseData(image_url=image_url, image_hash=image_hash)

    return web.Response(text=response_data.json())
