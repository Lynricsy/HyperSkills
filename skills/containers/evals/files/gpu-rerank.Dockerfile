# Build stage
FROM nvidia/cuda:13.0.1-devel-ubuntu24.04 AS build

RUN apt-get update && apt-get install -y \
      python3-pip python3-dev build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip3 install --break-system-packages -r requirements.txt
RUN python3 setup.py build_ext --inplace

# Make sure the driver is present so the container can talk to the GPU
RUN apt-get update && apt-get install -y nvidia-driver-550 \
    && rm -rf /var/lib/apt/lists/*

# Runtime stage
FROM python:3.12-slim

WORKDIR /app
COPY --from=build /app /app
COPY --from=build /usr/lib/python3/dist-packages /usr/lib/python3/dist-packages

ENV MODEL_DIR=/models

CMD python3 -m rerank.server --model $MODEL_DIR --port 8080
