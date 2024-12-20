FROM python:3.9-slim

WORKDIR /app

COPY server.py ./
COPY order_pb2.py ./
COPY order_pb2_grpc.py ./

RUN pip install grpcio grpcio-tools

CMD ["python", "server.py"]
