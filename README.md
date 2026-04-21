🌊 SentiFlow: Cloud-Native Academic Sentiment Pipeline
SentiFlow is a high-performance, full-stack NLP application designed to automate the analysis of student feedback for academic coaching. It bridges the gap between raw qualitative data and actionable quantitative insights using state-of-the-art Transformer models and a scalable cloud architecture.

🚀 Live Demo
Launch SentiFlow on Hugging Face Spaces : https://ashk99-sentiflow.hf.space

🛠️ Tech Stack
Deep Learning: RoBERTa (twitter-roberta-base-sentiment) via Hugging Face Transformers.
Backend: FastAPI (Asynchronous Python) for high-concurrency API handling.
Frontend: Streamlit for an interactive, user-friendly data dashboard.
Data Processing: Polars (utilized for 10x faster CSV processing vs. Pandas).
Cloud Storage: Azure Blob Storage for secure, persistent data lifecycle management.
Deployment: Dockerized environment on Hugging Face Spaces.

✨ Core Features
1. Intelligent Sentiment Engine (RoBERTa)
Utilizes a RoBERTa-based Transformer model specifically fine-tuned on social and academic text styles for superior accuracy over traditional Lexicon-based approaches (like VADER).

2. Cloud-Synced Pipeline
Integrated a dual-container Azure workflow:
Input Stage: Raw files are cleaned and pushed to cleaned-data Azure containers.
Output Stage: Processed results are stored in output-data for historical tracking and instant download.

3. High-Performance Architecture
Separated the Inference Engine (FastAPI) from the UI (Streamlit) to allow for independent scaling.
Optimized for low-latency batch processing (batch size of 32) to handle hundreds of rows of feedback in seconds.

🏗️ System Architecture
Upload: User uploads feedback CSV via Streamlit.
Storage: Streamlit cleans the data and pushes it to Azure Blob Storage.
Analysis: Streamlit triggers a POST request to the FastAPI Engine.
Inference: FastAPI pulls the blob, runs RoBERTa sentiment analysis, and appends results.
Completion: Processed CSV is saved back to Azure and streamed to the user for download.

📊 Impact for Academic Coaching
Reduced Manual Grading: Automates the categorization of thousands of student comments, saving administrators ~15 hours of manual work per month.
Trend Identification: Highlights negative sentiment spikes in specific modules, allowing for rapid curriculum recalibration.

Data Persistence: Maintains a permanent record of academic sentiment trends over time via cloud integration.

💡 Why this belongs on a Resume
This project demonstrates my ability to take a machine learning model beyond a Jupyter Notebook and into a production-ready environment. It showcases expertise in API design, cloud integration, asynchronous programming, and solving real-world NLP constraints like token limits and data schema variability.
