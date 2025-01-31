#!/bin/bash
gunicorn main:app \
    --workers 6 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:80 \
    --backlog 2048 \
    --worker-connections 1000 \
    --keep-alive 5 \
    --timeout 300