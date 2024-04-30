import asyncio
import logging

from aiohttp import web
from pydantic import BaseModel

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server import models, settings
from ray_on_golem.server.services import RayService, YagnaService
from ray_on_golem.utils import raise_graceful_exit
from ray_on_golem.version import get_version

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


def reject_if_shutting_down(func):
    async def wrapper(request: web.Request) -> web.Response:
        if request.app.get("shutting_down"):
            return web.HTTPBadRequest(reason="Action not allowed while server is shutting down!")

        return await func(request)

    return wrapper


def json_response(model_obj: BaseModel) -> web.Response:
    """Return a JSON web response based on the provided pydantic model."""
    return web.json_response(text=model_obj.json())


@routes.view(settings.URL_STATUS)
async def status(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    return json_response(
        models.WebserverStatus(
            version=get_version(),
            datadir=str(ray_service.datadir),
            shutting_down=request.app.get("shutting_down", False),
            self_shutdown=request.app.get("self_shutdown"),
            server_warnings=ray_service.get_warning_messages(),
        )
    )


@routes.post(settings.URL_GET_WALLET_STATUS)
async def get_wallet_status(request: web.Request) -> web.Response:
    yagna_service: YagnaService = request.app["yagna_service"]

    request_data = models.GetWalletStatusRequestData.parse_raw(await request.text())

    try:
        payment_status = await yagna_service.prepare_funds(
            request_data.payment_network, request_data.payment_driver
        )
        yagna_output = await yagna_service.fetch_payment_status(
            request_data.payment_network, request_data.payment_driver
        )
        wallet_address = await yagna_service.fetch_wallet_address()
    except RayOnGolemError as e:
        raise web.HTTPBadRequest(reason=str(e))

    return json_response(
        models.GetWalletStatusResponseData(
            wallet_address=wallet_address,
            yagna_payment_status_output=yagna_output,
            yagna_payment_status=payment_status,
        )
    )


@routes.post(settings.URL_NON_TERMINATED_NODES)
async def non_terminated_nodes_ids(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.NonTerminatedNodesRequestData.parse_raw(await request.text())

    nodes_ids = await ray_service.get_non_terminated_nodes_ids(
        cluster_name=request_data.cluster_name,
        tags_to_match=request_data.tags,
    )

    return json_response(models.NonTerminatedNodesResponseData(nodes_ids=nodes_ids))


@routes.post(settings.URL_IS_RUNNING)
async def is_node_running(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    is_running = await ray_service.is_node_running(
        cluster_name=request_data.cluster_name,
        node_id=request_data.node_id,
    )

    return json_response(models.IsRunningResponseData(is_running=is_running))


@routes.post(settings.URL_GET_CLUSTER_DATA)
async def get_cluster_data(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.GetClusterDataRequestData.parse_raw(await request.text())

    cluster_data = await ray_service.get_cluster_data(
        cluster_name=request_data.cluster_name,
    )

    return json_response(models.GetClusterDataResponseData(cluster_data=cluster_data))


@routes.post(settings.URL_IS_TERMINATED)
async def is_node_terminated(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    is_terminated = await ray_service.is_node_terminated(
        cluster_name=request_data.cluster_name,
        node_id=request_data.node_id,
    )

    return json_response(models.IsTerminatedResponseData(is_terminated=is_terminated))


@routes.post(settings.URL_NODE_TAGS)
async def get_node_tags(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    node_tags = await ray_service.get_node_tags(
        cluster_name=request_data.cluster_name,
        node_id=request_data.node_id,
    )

    return json_response(models.GetNodeTagsResponseData(tags=node_tags))


@routes.post(settings.URL_INTERNAL_IP)
async def get_node_internal_ip(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    ip_address = await ray_service.get_node_internal_ip(
        cluster_name=request_data.cluster_name,
        node_id=request_data.node_id,
    )

    return json_response(models.GetNodeIpAddressResponseData(ip_address=ip_address))


@routes.post(settings.URL_SET_NODE_TAGS)
async def set_node_tags(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SetNodeTagsRequestData.parse_raw(await request.text())

    await ray_service.set_node_tags(
        cluster_name=request_data.cluster_name,
        node_id=request_data.node_id,
        tags=request_data.tags,
    )

    return json_response(models.EmptyResponseData())


@routes.post(settings.URL_REQUEST_NODES)
@reject_if_shutting_down
async def request_nodes(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.RequestNodesRequestData.parse_raw(await request.text())

    requested_nodes = await ray_service.request_nodes(
        cluster_name=request_data.cluster_name,
        provider_config=request_data.provider_parameters,
        node_config=request_data.node_config,
        count=request_data.count,
        tags=request_data.tags,
    )

    return json_response(models.RequestNodesResponseData(requested_nodes=requested_nodes))


@routes.post(settings.URL_TERMINATE_NODE)
@reject_if_shutting_down
async def terminate_node(request: web.Request) -> web.Response:
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    terminated_nodes = await ray_service.terminate_node(
        cluster_name=request_data.cluster_name,
        node_id=request_data.node_id,
    )

    return json_response(models.TerminateNodeResponseData(terminated_nodes=terminated_nodes))


@routes.post(settings.URL_GET_SSH_PROXY_COMMAND)
async def get_ssh_proxy_command(request):
    ray_service: RayService = request.app["ray_service"]

    request_data = models.SingleNodeRequestData.parse_raw(await request.text())

    ssh_proxy_command = await ray_service.get_ssh_proxy_command(
        cluster_name=request_data.cluster_name,
        node_id=request_data.node_id,
    )

    return json_response(models.GetSshProxyCommandResponseData(ssh_proxy_command=ssh_proxy_command))


@routes.post(settings.URL_GET_OR_CREATE_DEFAULT_SSH_KEY)
async def get_or_create_ssh_key(request):
    ray_service: RayService = request.app["ray_service"]

    request_data = models.GetOrCreateDefaultSshKeyRequestData.parse_raw(await request.text())

    priv, pub = await ray_service.get_or_create_default_ssh_key(
        cluster_name=request_data.cluster_name
    )

    return json_response(
        models.GetOrCreateDefaultSshKeyResponseData(
            ssh_private_key_base64=priv,
            ssh_public_key_base64=pub,
        )
    )


@routes.post(settings.URL_SHUTDOWN)
async def shutdown(request):
    ray_service: RayService = request.app["ray_service"]

    shutdown_request = models.ShutdownRequestData.parse_raw(await request.text())

    if not (shutdown_request.ignore_self_shutdown or request.app["self_shutdown"]):
        shutdown_state = models.ShutdownState.NOT_ENABLED
    elif ray_service.is_any_node_running():
        if shutdown_request.force_shutdown:
            shutdown_state = models.ShutdownState.FORCED_SHUTDOWN
        else:
            shutdown_state = models.ShutdownState.CLUSTER_NOT_EMPTY
    else:
        shutdown_state = models.ShutdownState.WILL_SHUTDOWN

    if shutdown_state in (models.ShutdownState.WILL_SHUTDOWN, models.ShutdownState.FORCED_SHUTDOWN):
        shutdown_seconds = shutdown_request.shutdown_delay
        if shutdown_seconds:
            logger.info(
                "Received a %sself-shutdown request, exiting in %s seconds...",
                "forced " if models.ShutdownState.FORCED_SHUTDOWN else "",
                shutdown_seconds,
            )
        else:
            logger.info(
                "Initiating a %sshutdown immediately...",
                "forced " if models.ShutdownState.FORCED_SHUTDOWN else "",
            )
        loop = asyncio.get_event_loop()
        loop.call_later(shutdown_seconds, raise_graceful_exit)
        request.app["shutting_down"] = True

    return json_response(models.ShutdownResponseData(shutdown_state=shutdown_state))
