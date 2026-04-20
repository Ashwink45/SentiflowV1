---
title: SentiFlow
emoji: 📈
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
license: mit
---

# 📊 SentiFlow: Sentiment Analysis Dashboard

This is a research-focused application that performs sentiment analysis on data pulled from **Azure Blob Storage** and stores results in **Azure SQL**.

## 🛠️ Tech Stack
- **Frontend:** Streamlit
- **Backend Engine:** FastAPI (Local)
- **Model:** RoBERTa (`cardiffnlp/twitter-roberta-base-sentiment`)
- **Cloud:** Azure (Storage & SQL)
- **Deployment:** Hugging Face Spaces (Docker)

## 📜 Attribution & License
- **Model:** Sentiment analysis is powered by the [CardiffNLP RoBERTa model](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment).
- **Code License:** [MIT](https://opensource.org/licenses/MIT)

## 🚀 How it Works
This Space uses a multi-process Docker container to run both the Streamlit UI and a FastAPI backend on a single 16GB RAM instance.