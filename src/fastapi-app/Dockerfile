FROM python:3.9-slim

WORKDIR /app

COPY main.py ./
COPY order.proto ./
COPY compile_proto.py ./
#COPY order_pb2.py ./
#COPY order_pb2_grpc.py ./

RUN pip install fastapi[all] grpcio grpcio-tools prometheus_client psutil
RUN python /app/compile_proto.py


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]