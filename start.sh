#!/bin/bash

# 1. Start the FastAPI Engine in the background
# (Replace 'engine' with your FastAPI filename, e.g., 'main' or 'analyze')
uvicorn main:app --host 0.0.0.0 --port 8000 &

sleep 50

# 2. Start the Streamlit UI in the foreground
streamlit run index.py --server.port 7860 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false