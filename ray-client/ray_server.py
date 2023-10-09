
from concurrent import futures
import logging

import grpc
import json

from src.ray.protobuf import gcs_service_pb2
from src.ray.protobuf import gcs_service_pb2_grpc

CLUSTER_ID = b"zasadzka nie spi z byle Kim."

kvstore = dict(
    {
        "session:session_name": b"xxx",
        "session:temp_dir": b"/tmp/ray/xxx",
        "cluster:CLUSTER_METADATA": json.dumps(None).encode("ascii"),
    }
)

nodes = list()


class InternalKV(gcs_service_pb2_grpc.InternalKVGcsServiceServicer):
    def InternalKVGet(self, request: gcs_service_pb2.InternalKVGetRequest, context):
        print(self, "InternalKVGet", request.key, request.namespace)
        dict_key = f"{request.namespace.decode('ascii')}:{request.key.decode('ascii')}"
        value = kvstore.get(dict_key, b"")
        print("InternalKVGet", dict_key, value)
        return gcs_service_pb2.InternalKVGetReply(
            status=gcs_service_pb2.GcsStatus(code=0, message="ok"),
            value=value
        )

    def InternalKVPut(self, request: gcs_service_pb2.InternalKVPutRequest, context):
        print(self, "InternalKVPut", request)
        kvstore[f"{request.namespace}:{request.key}"] = request.value
        return gcs_service_pb2.InternalKVPutReply(
            status=gcs_service_pb2.GcsStatus(code=0, message="ok"),
            added_num=1,
        )


class GCS(gcs_service_pb2_grpc.NodeInfoGcsServiceServicer):

    def GetInternalConfig(self, request: gcs_service_pb2.GetInternalConfigRequest, context):
        print(self, "GetInternalConfig")
        return gcs_service_pb2.GetInternalConfigReply(
            status=gcs_service_pb2.GcsStatus(code=0, message="ok"),
            config=json.dumps({}),
        )

    def GetClusterId(self, request: gcs_service_pb2.GetClusterIdRequest, context):
        print(self, "GetClusterId")
        return gcs_service_pb2.GetClusterIdReply(
            status=gcs_service_pb2.GcsStatus(code=0, message="ok"),
            cluster_id=CLUSTER_ID,
        )

    def GetAllNodeInfo(self, request: gcs_service_pb2.GetAllNodeInfoRequest, context):
        print(self, "GetAllNodeInfo", request)
        return gcs_service_pb2.GetAllNodeInfoReply(
            status=gcs_service_pb2.GcsStatus(code=0, message="ok"),
            node_info_list=nodes,
        )

    def RegisterNode(self, request: gcs_service_pb2.RegisterNodeRequest, context):
        print(self, "RegisterNode", request.node_info)
        nodes.append(request.node_info)
        return gcs_service_pb2.RegisterNodeReply(
            status=gcs_service_pb2.GcsStatus(code=0, message="ok"),
        )

    def CheckAlive(self, request: gcs_service_pb2.CheckAliveRequest, context):
        print(self, "CheckAlive", request)
        return gcs_service_pb2.CheckAliveReply(
            status=gcs_service_pb2.GcsStatus(code=0, message="ok"),
            ray_version="2.7",
            raylet_alive=[True],
        )



def serve():
    port = "6379"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gcs_service_pb2_grpc.add_InternalKVGcsServiceServicer_to_server(InternalKV(), server)
    gcs_service_pb2_grpc.add_NodeInfoGcsServiceServicer_to_server(GCS(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
