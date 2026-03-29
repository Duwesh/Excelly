#!/bin/bash

echo "================================="
echo "Starting Excel Analysis Backend"
echo "================================="

echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r my_agent/requirements.txt

echo "Starting sandbox server..."
python run_sandbox_server.py &

echo "Starting FastAPI backend..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}