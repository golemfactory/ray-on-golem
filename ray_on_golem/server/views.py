import asyncio
import logging

from aiohttp import web

from ray_on_golem.server import models, settings
from ray_on_golem.server.models import ShutdownState
from ray_on_golem.server.services import RayService
from ray_on_golem.utils import raise_graceful_exit

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


def reject_if_shutting_down(func):
    async def wrapper(request: web.Request) -> web.Response:
        if request.app.get("shutting_down"):
            return web.HTTPBadRequest(text="Action not allowed while server is shutting down!")

        return await func(request)

    return wrapper


# FIXME: This route should be a default root URL with basic server info instead of
#  custom URL with custom payload
@routes.get(settings.URL_HEALTH_CHECK)
async def health_check(request: web.Request) -> web.Response:
    response_data = models.HealthCheckResponseData(
        is_shutting_down=request.app.get("shutting_down", False)
    )

    return web.Response(text=response_data.json())


@routes.post(settings.URL_CREATE_CLUSTER)
async def create_cluster(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.CreateClusterRequestData.parse_raw(await request.text())

    (
        is_cluster_just_created,
        wallet_address,
        yagna_payment_status_output,
    ) = await ray_service.create_cluster(provider_config=request_data)

    response_data = models.CreateClusterResponseData(
        is_cluster_just_created=is_cluster_just_created,
        wallet_address=wallet_address,
        yagna_payment_status_output=yagna_payment_status_output,
    )

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


@routes.post(settings.URL_GET_CLUSTER_DATA)
async def get_cluster_data(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    models.GetClusterDataRequestData.parse_raw(await request.text())

    cluster_data = await ray_service.get_cluster_data()

    response_data = models.GetClusterDataResponseData(cluster_data=cluster_data)

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


@routes.post(settings.URL_REQUEST_NODES)
@reject_if_shutting_down
async def request_nodes(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.RequestNodesRequestData.parse_raw(await request.text())

    requested_nodes = await ray_service.request_nodes(
        request_data.node_config, request_data.count, request_data.tags
    )

    response_data = models.RequestNodesResponseData(requested_nodes=requested_nodes)

    return web.Response(text=response_data.json())


@routes.post(settings.URL_TERMINATE_NODE)
@reject_if_shutting_down
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


@routes.post(settings.URL_SELF_SHUTDOWN)
async def self_shutdown(request):
    ray_service: RayService = request.app["ray_service"]

    models.SelfShutdownRequestData.parse_raw(await request.text())

    if not request.app["self_shutdown"]:
        shutdown_state = ShutdownState.NOT_ENABLED
    elif await ray_service.get_non_terminated_nodes_ids():
        shutdown_state = ShutdownState.CLUSTER_NOT_EMPTY
    else:
        shutdown_state = ShutdownState.WILL_SHUTDOWN

    if shutdown_state == ShutdownState.WILL_SHUTDOWN:
        shutdown_seconds = int(settings.RAY_ON_GOLEM_SHUTDOWN_DELAY.total_seconds())
        logger.info(f"Received a self-shutdown request, exiting in {shutdown_seconds} seconds...")
        loop = asyncio.get_event_loop()
        loop.call_later(shutdown_seconds, raise_graceful_exit)
        request.app["shutting_down"] = True

    response_data = models.SelfShutdownResponseData(shutdown_state=shutdown_state)

    return web.Response(text=response_data.json())
