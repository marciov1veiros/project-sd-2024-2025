from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from starlette.responses import Response
from typing import List
import grpc
import order_pb2
import order_pb2_grpc
import logging
import os
import psutil
import time



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_app")

app = FastAPI()

# Custom metrics
REQUEST_COUNT = Counter('http_request_total', 'Total HTTP Requests', ['method', 'status', 'path'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Duration', ['method', 'status', 'path'])
REQUEST_IN_PROGRESS = Gauge('http_requests_in_progress', 'HTTP Requests in progress', ['method', 'path'])
GRPC_REQUEST_COUNT = Counter('grpc_request_total', 'Total gRPC Requests', ['method', 'status'])
GRPC_REQUEST_LATENCY = Histogram('grpc_request_duration_seconds', 'gRPC Request Duration', ['method', 'status'])
ITEMS_SOLD = Counter('items_sold_total', 'Total Items Sold')
GRPC_CONNECTIONS = Gauge('grpc_connections', 'Number of active gRPC connections', ['server'])

# System metrics
CPU_USAGE = Gauge('process_cpu_usage', 'Current CPU usage in percent')
MEMORY_USAGE = Gauge('process_memory_usage_bytes', 'Current memory usage in bytes')

def update_system_metrics():
    CPU_USAGE.set(psutil.cpu_percent())
    MEMORY_USAGE.set(psutil.Process().memory_info().rss)

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class OrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItem]

@app.post("/order-products")
async def order_products(order: OrderRequest):
    #grpc.insecure_channel("grpc-server1:50051")
    #grpc.insecure_channel(f"{os.getenv('GRPC_SERVER1_HOST', 'localhost')}:50051")
    with grpc.insecure_channel(f"{os.getenv('GRPC_SERVER1_HOST', 'localhost')}:50051") as channel:
        stub = order_pb2_grpc.OrderServiceStub(channel)

        # Create a request (order)
        order = order_pb2.OrderMessage(
            customer_id=order.customer_id,
            items=[
                order_pb2.OrderItem(product_id=item.product_id, quantity=item.quantity, price=item.price) for item in order.items
            ]
        )

        # Call the method to Submit order
        response = stub.SubmitOrder(order)

        return {
            "confirmation_id": response.confirmation_id,
            "message": response.message
        }

@app.get("/get-products")
async def get_products():
    grpc_server = f"{os.getenv('GRPC_SERVER2_HOST', 'localhost')}:8080"
    GRPC_CONNECTIONS.labels(server=grpc_server).inc()  # Increment active connections
    start_time = time.time()

    #grpc.insecure_channel("grpc-server2:8080")
    #grpc.insecure_channel(f"{os.getenv('GRPC_SERVER2_HOST', 'localhost')}:8080")
    try:
        with grpc.insecure_channel(grpc_server) as channel:
            stub = order_pb2_grpc.ProductServiceStub(channel)
            grpc_method = "GetProducts"

            # Create a request (order)
            request = order_pb2.Empty()

            # Call the method to Submit order
            response = stub.GetProducts(request)

            # Update gRPC metrics
            duration = time.time() - start_time
            GRPC_REQUEST_COUNT.labels(method=grpc_method, status="success").inc()
            GRPC_REQUEST_LATENCY.labels(method=grpc_method, status="success").observe(duration)

            # Serialize the response
            products = [
                {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "description": product.description,
                    "image": product.image
                } for product in response.products
            ]

            return products
    except grpc.RpcError as e:
        # Update metrics for gRPC failure
        duration = time.time() - start_time
        GRPC_REQUEST_COUNT.labels(method=grpc_method, status="failure").inc()
        GRPC_REQUEST_LATENCY.labels(method=grpc_method, status="failure").observe(duration)
        raise HTTPException(status_code=500, detail="Failed to fetch products")
    finally:
        GRPC_CONNECTIONS.labels(server=grpc_server).dec()  # Decrement active connections
    
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    method = request.method
    path = request.url.path

    REQUEST_IN_PROGRESS.labels(method=method, path=path).inc()
    
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    status = response.status_code
    REQUEST_COUNT.labels(method=method, status=status, path=path).inc()
    REQUEST_LATENCY.labels(method=method, status=status, path=path).observe(duration)
    REQUEST_IN_PROGRESS.labels(method=method, path=path).dec()

    return response

@app.get("/metrics")
async def metrics():
    update_system_metrics()
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
