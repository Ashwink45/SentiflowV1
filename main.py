from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import polars as pl  # Switched to Polars for speed
import io
import os
from transformers import pipeline
from azure.storage.blob import BlobServiceClient
from config import CONN_STR as conn_str

app = FastAPI(title="Sentiment Analysis API")

# 🚀 STEP 1: GLOBAL LOAD (The "Once and Done" Move)
# This runs once when you start the server. 
# It stays in your RAM so it's ready for instant use.
print("--- 🤖 Loading RoBERTa Model into RAM... ---")
classifier = pipeline(
    "sentiment-analysis", 
    model="cardiffnlp/twitter-roberta-base-sentiment",
    device=-1 # Use -1 for CPU (common for local/Render)
)
blob_service_client = BlobServiceClient.from_connection_string(conn_str)

LABEL_MAPPING = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}
print("--- ✅ Model Loaded and Ready! ---")

class PipelineInput(BaseModel):
    pipeline_id: str

@app.get("/")
def home():
    return {"message": "Server is running! Model is pre-loaded."}

@app.post("/analyze")
def analyze(data: PipelineInput):
    try:
        
        # ------------------ FETCH CLEANED FILE ------------------
        blob_name = f"cleaned_{data.pipeline_id}.csv"
        blob_client = blob_service_client.get_blob_client(container="cleaned-data", blob=blob_name)
        
        raw_data = blob_client.download_blob().readall()
        
        # ⚡ POLARS: Fast loading
        df = pl.read_csv(raw_data)
        
        # Safety check
        if "Feedback" not in df.columns:
            raise Exception("Feedback column missing")

        # Convert to list for the model
        texts = df["Feedback"].fill_null("").cast(pl.Utf8).to_list()

        # 🚀 STEP 2: INSTANT INFERENCE
        # Since the model is already in RAM, this starts IMMEDIATELY.
        # We use a batch_size of 32 to feed the CPU efficiently.
        print(f"--- 🧠 Analyzing {len(texts)} rows... ---")
        raw_results = classifier(texts, batch_size=32, truncation=True)
        
        # Map labels to human words
        sentiments = [LABEL_MAPPING[res['label']] for res in raw_results]

        # Add back to dataframe
        df = df.with_columns(pl.Series(name="Sentiment", values=sentiments))

        # ------------------ SAVE & UPLOAD ------------------
        # Polars write_csv is much faster than Pandas to_csv
        csv_data = df.write_csv().encode('utf-8')
        output_blob_name = f"output_{data.pipeline_id}.csv"

        output_blob_client = blob_service_client.get_blob_client(container="output-data", blob=output_blob_name)
        output_blob_client.upload_blob(csv_data, overwrite=True)

        print(f"--- ✅ Analysis Complete for {data.pipeline_id} ---")

        # ------------------ STREAM RESPONSE ------------------
        return StreamingResponse(
            io.BytesIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={output_blob_name}"}
        )

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))