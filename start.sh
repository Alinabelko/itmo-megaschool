#!/bin/bash
gunicorn main:app --workers 6 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 