pip install -e ./
python3 -m grpc_tools.protoc -I./chat/grpc --python_out=./chat/grpc --pyi_out=./chat/grpc --grpc_python_out=./chat/grpc ./chat/grpc/proto.proto
