"""The Python implementation of the GRPC helloworld.Greeter client."""

import logging

import grpc
from src.ray.protobuf import gcs_service_pb2
from src.ray.protobuf import gcs_service_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    print("Will try to greet world ...")
    with grpc.insecure_channel("localhost:6379") as channel:
        stub = gcs_service_pb2_grpc.NodeInfoGcsServiceStub(channel)
        response:gcs_service_pb2.GetClusterIdReply = stub.GetClusterId(gcs_service_pb2.GetClusterIdRequest())
    print("Greeter client received: " + str(response.cluster_id))


if __name__ == "__main__":
    logging.basicConfig()
    run()
