# SentiFlow — Automated Sentiment Analysis Platform

SentiFlow is a cloud-integrated sentiment analysis platform that allows users to upload CSV-based feedback datasets and automatically generate sentiment predictions and interactive analytics dashboards using Transformer-based NLP models.

The platform uses a RoBERTa model from Hugging Face Transformers for sentiment classification and integrates FastAPI, Streamlit, Azure Blob Storage, Azure SQL, and Docker to support scalable preprocessing, inference, storage, and deployment workflows.

## System Workflow

1. Users upload feedback datasets through the Streamlit interface
2. Data is cleaned and processed through automated preprocessing pipelines
3. Files are stored and managed using Azure Blob Storage
4. FastAPI handles sentiment inference using the RoBERTa model
5. Processed results and analytics are generated in real time
6. User data and processed workflows are maintained using Azure SQL

## Tech Stack

Python, FastAPI, Streamlit, Hugging Face Transformers, RoBERTa, Azure Blob Storage, Azure SQL, Docker, REST APIs

Live Demo:
https://ashk99-sentiflow.hf.space
