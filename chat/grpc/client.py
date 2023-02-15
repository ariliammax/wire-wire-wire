import grpc
import proto_pb2
import proto_pb2_grpc

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = proto_pb2_grpc.GreeterStub(channel)
        response = stub.SayHello(proto_pb2.HelloRequest(name='you'))
    print(response.message)
