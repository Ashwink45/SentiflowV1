import polars as pl
import uuid
from azure.storage.blob import BlobServiceClient
import requests  # top of file
from config import CONN_STR as conn_str
import os 

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://host.docker.internal:8000/analyze")

# 🔐 Azure connection string


def process_blob(blob_name,pipeline_id):

    blob_service_client = BlobServiceClient.from_connection_string(conn_str)

    # ------------------ DOWNLOAD FROM raw-data ------------------
    blob_client = blob_service_client.get_blob_client(
        container="raw-data",
        blob=blob_name
    )

    data = blob_client.download_blob().readall()

    df = pl.read_csv(data)

    print("Original columns:", df.columns)

    # ------------------ CLEANING ------------------

    df = df.rename({c: c.strip() for c in df.columns})

    # 2. 🔹 Select only the "Golden Pair"
    # We use a list of columns we want to keep
    target_columns = ["Date", "Feedback"]
    
    # Safety check: only select if they actually exist to prevent crashing
    existing_targets = [c for c in target_columns if c in df.columns]
    df = df.select(existing_targets)

    # 3. 🔹 Drop null values in Feedback
    if "Feedback" in df.columns:
        df = df.filter(pl.col("Feedback").is_not_null())

    print("Remaining columns:", df.columns)
    

    # ------------------ SAVE TO MEMORY ------------------
    cleaned_csv_string = df.write_csv()

    # ------------------ NEW FILE NAME ------------------
    new_blob_name = f"cleaned_{pipeline_id}.csv"

    # ------------------ UPLOAD TO cleaned-data ------------------
    output_blob_client = blob_service_client.get_blob_client(
        container="cleaned-data",
        blob=new_blob_name
    )

    output_blob_client.upload_blob(cleaned_csv_string.encode('utf-8'), overwrite=True)

    response = requests.post(FASTAPI_URL, json={"pipeline_id": pipeline_id}, timeout=300)
    if response.status_code == 200:
        print("✅ ML pipeline triggered successfully")
    else:
        print(f"❌ ML trigger failed: {response.status_code} - {response.text}")

    # ------------------ RETURN FULL PATH ------------------
    blob_url = output_blob_client.url

    print("✅ Uploaded cleaned file:", blob_url)

    return {
        "blob_name": new_blob_name,
        "blob_url": blob_url,
        "pipeline_id": pipeline_id
    }