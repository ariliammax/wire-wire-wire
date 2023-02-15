from concurrent import futures

import grpc
import proto_pb2
import proto_pb2_grpc

class Greeter(proto_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return proto_pb2.HelloReply(message='Hello, %s!' % request.name)

if __name__ == '__main__':
    port = '50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    proto_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    server.wait_for_termination()
