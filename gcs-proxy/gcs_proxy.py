import argparse
from concurrent import futures
import logging
from typing import Optional

import grpc

# from src.ray.protobuf import gcs_service_pb2
from src.ray.protobuf import gcs_service_pb2_grpc


class GCS:
    __instance: Optional["GCS"]
    gcs_address: str
    gcs_port: int

    def __init__(self, gcs_address: str, gcs_port: int):
        print(f"Using GCS on {gcs_address}:{gcs_port}")
        self.gcs_address = gcs_address
        self.gcs_port = gcs_port
        GCS.__instance = self

    @classmethod
    def get(cls) -> "GCS":
        return cls.__instance

    def call(self, stub_class, method_name, *args, **kwargs):
        print(f"calling: {stub_class.__name__}.{method_name}({args}, {kwargs})")
        with grpc.insecure_channel(f"{self.gcs_address}:{self.gcs_port}") as channel:
            stub = stub_class(channel)
            method = getattr(stub, method_name)
            response = method(*args, **kwargs)
            print(f"response: {stub_class.__name__}.{method_name}({args}, {kwargs})\n{response}")
            return response


class InternalKV(gcs_service_pb2_grpc.InternalKVGcsServiceServicer):
    stub_class = gcs_service_pb2_grpc.InternalKVGcsServiceStub

    def InternalKVGet(self, request, _context):
        return GCS.get().call(self.stub_class, "InternalKVGet", request)

    def InternalKVPut(self, request, _context):
        return GCS.get().call(self.stub_class, "InternalKVPut", request)


class NodeInfo(gcs_service_pb2_grpc.NodeInfoGcsServiceServicer):
    stub_class = gcs_service_pb2_grpc.NodeInfoGcsServiceStub

    def GetInternalConfig(self, request, _context):
        return GCS.get().call(self.stub_class, "GetInternalConfig", request)

    def GetClusterId(self, request, _context):
        return GCS.get().call(self.stub_class, "GetClusterId", request)

    def GetAllNodeInfo(self, request, _context):
        return GCS.get().call(self.stub_class, "GetAllNodeInfo", request)

    def RegisterNode(self, request, _context):
        return GCS.get().call(self.stub_class, "RegisterNode", request)

    def CheckAlive(self, request, _context):
        return GCS.get().call(self.stub_class, "CheckAlive", request)

    def DrainNode(self, request, _context):
        return GCS.get().call(self.stub_class, "DrainNode", request)


def serve(port: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gcs_service_pb2_grpc.add_InternalKVGcsServiceServicer_to_server(InternalKV(), server)
    gcs_service_pb2_grpc.add_NodeInfoGcsServiceServicer_to_server(NodeInfo(), server)
    server.add_insecure_port("[::]:" + str(port))
    server.start()
    print("Server started, listening on " + str(port))
    server.wait_for_termination()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Ray GCS Debug proxy")
    parser.add_argument("-g", "--gcs-address", type=str, default="127.0.0.1")
    parser.add_argument("-p", "--gcs-port", type=int, default=6379)
    parser.add_argument("-l", "--listen-port", type=int, default=6380)
    return parser


if __name__ == "__main__":
    logging.basicConfig()
    parser = build_parser()
    args = parser.parse_args()
    print(args)
    GCS(args.gcs_address, args.gcs_port)
    serve(args.listen_port)
