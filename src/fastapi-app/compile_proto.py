import grpc_tools.protoc

grpc_tools.protoc.main((
    '',
    '--python_out=./',
    '--grpc_python_out=./',
    '--proto_path=',
    'order.proto',
))