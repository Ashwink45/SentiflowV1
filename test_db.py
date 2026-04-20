# test_db.py
from db import get_connection

try:
    conn = get_connection()
    print("✅ Connected to Azure SQL successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")

# test_db_functions.py
from db import register_user, verify_user, insert_file, insert_pipeline_run, fetch_user_runs

# 1. Register a test user
print("Testing register_user...")
user_id = register_user("ashwin", "ashwin@test.com", "test123")
print(f"✅ Registered user_id: {user_id}")

# 2. Verify login
print("\nTesting verify_user...")
user = verify_user("ashwin", "test123")
print(f"✅ Logged in as: {user}")

# 3. Insert a file record
print("\nTesting insert_file...")
file_id = insert_file(
    user_id=user["user_id"],
    original_file_name="feedback.csv",
    file_size_kb=24.5,
    row_count=500,
    raw_blob_name="upload_test-pipeline-id.csv"
)
print(f"✅ Inserted file_id: {file_id}")

# 4. Insert a pipeline run
print("\nTesting insert_pipeline_run...")
run_id = insert_pipeline_run(
    file_id=file_id,
    user_id=user["user_id"],
    pipeline_id="test-pipeline-id",
    positive_count=300,
    neutral_count=120,
    negative_count=80,
    output_blob_name="output_test-pipeline-id.csv"
)
print(f"✅ Inserted run_id: {run_id}")

# 5. Fetch user runs
print("\nTesting fetch_user_runs...")
runs = fetch_user_runs(user["user_id"])
for run in runs:
    print(f"✅ Run: {run['original_file_name']} | {run['pipeline_id']} | {run['status']}")