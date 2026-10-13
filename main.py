
import os
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

EMAIL = os.getenv("EMAIL", "24f2007761@ds.study.iitm.ac.in")

client_requests = defaultdict(deque)
LIMIT = 14
WINDOW = 10


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.monotonic()
    timestamps = client_requests[client_id]

    while timestamps and now - timestamps[0] >= WINDOW:
        timestamps.popleft()

    if len(timestamps) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    timestamps.append(now)
    return await call_next(request)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-6yddkz.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["X-Request-ID", "X-Client-Id", "Content-Type"],
)

# Add this last so it wraps CORS and all other middleware.
app.add_middleware(RequestIDMiddleware)
