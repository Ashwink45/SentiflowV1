
import bcrypt
from datetime import datetime
import uuid
import pyodbc
import os
import time
import socket

# ------------------ CONNECTION HELPER ------------------


def get_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

def diagnose_connection():
    print("\n" + "="*50)
    print("🔍 SENTIFLOW DATABASE DIAGNOSTIC TOOL (pyodbc)")
    print("="*50)

    server = os.getenv("DB_SERVER")
    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")

    print(f"📍 Server:   {server}")
    print(f"👤 User:     {user}")
    print(f"🗄️ Database: {db_name}")
    print(f"🔑 Password: {'[SET]' if pwd else '[EMPTY]'} (Length: {len(pwd) if pwd else 0})")

    # Network Check
    print("\n--- Network Layer Check ---")
    try:
        host = server.split(',')[0] if server and ',' in server else server
        ip = socket.gethostbyname(host)
        print(f"✅ DNS Resolved: {host} -> {ip}")
        with socket.create_connection((host, 1433), timeout=5):
            print("✅ Port 1433 reachable (Firewall OK)")
    except Exception as e:
        print(f"❌ Network Failure: {e}")
        return

    # Connection Attempt (Updated to pyodbc)
    print("\n--- DB Connection Check ---")
    try:
        conn = get_connection()
        print("🎉 CONNECTION SUCCESSFUL!")
        conn.close()
        return True
    except pyodbc.Error as e:
        # pyodbc errors are tuples; the second element is the message
        sqlstate = e.args[0]
        err_msg = e.args[1]
        print(f"\n🛑 SQLSTATE: {sqlstate}")
        
        if "18456" in err_msg:
            print("❌ INVALID CREDENTIALS")
        elif "40613" in err_msg:
            print("❌ DATABASE UNAVAILABLE (Cold Start)")
        else:
            print(f"❌ ERROR: {err_msg}")
    
    print("="*50 + "\n")
    return False

# ==============================================================
# 1. REGISTER USER
# Insert a new user into the users table
# Returns: user_id if success, None if username/email exists
# ==============================================================
def register_user(username, email, password):
    token = str(uuid.uuid4())
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        conn = get_connection()          # ✅ create connection
        cursor = conn.cursor()           # ✅ create cursor

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, is_verified, verification_token)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, hashed, 0, token))

        conn.commit()
        conn.close()                     # ✅ always close connection

        return token

    except Exception as e:
        print("❌ register_user error:", e)
        return None


# ==============================================================
# 2. VERIFY USER (LOGIN)
# Check username + password against the database
# Returns: user dict if valid, None if invalid
# ==============================================================
def verify_user(username, password):
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, email, password_hash, is_verified
            FROM users
            WHERE username = ?
        """, (username,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # 🔥 FIX: Handle both bytes and string
        stored_hash = (
            row.password_hash 
            if isinstance(row.password_hash, bytes) 
            else row.password_hash.encode("utf-8")
        )

        password_match = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash
        )

        if password_match:
            return {
                "user_id":  row.user_id,
                "username": row.username,
                "email":    row.email,
                "is_verified": row.is_verified
            }

        return None

    except Exception as e:
        print(f"❌ verify_user error: {e}")
        return None


# ==============================================================
# 3. INSERT FILE RECORD
# Called after file is uploaded to raw-data blob
# Returns: file_id if success, None if error
# ==============================================================
def insert_file(user_id, original_file_name, file_size_kb, row_count, raw_blob_name):
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO files (user_id, original_file_name, file_size_kb, row_count, raw_blob_name)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, original_file_name, file_size_kb, row_count, raw_blob_name))

        conn.commit()

        # Fetch the newly created file_id
        cursor.execute("""
            SELECT file_id FROM files
            WHERE user_id = ? AND raw_blob_name = ?
        """, (user_id, raw_blob_name))

        row = cursor.fetchone()
        conn.close()

        return row.file_id if row else None

    except Exception as e:
        print(f"❌ insert_file error: {e}")
        return None


# ==============================================================
# 4. INSERT PIPELINE RUN
# Called after ML pipeline completes
# Returns: run_id if success, None if error
# ==============================================================
def insert_pipeline_run(file_id, user_id, pipeline_id,
                        positive_count, neutral_count, negative_count,
                        output_blob_name):
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        now = datetime.utcnow()

        cursor.execute("""
            INSERT INTO pipeline_runs (
                file_id, user_id, pipeline_id,
                status,
                positive_count, neutral_count, negative_count,
                output_blob_name,
                created_at,
                completed_at
            )
            VALUES (?, ?, ?, 'completed', ?, ?, ?, ?, ?, ?)
        """, (
            file_id, user_id, pipeline_id,
            positive_count, neutral_count, negative_count,
            output_blob_name,
            now,
            now
        ))

        conn.commit()

        cursor.execute("""
            SELECT TOP 1 run_id FROM pipeline_runs
            WHERE pipeline_id = ?
            ORDER BY completed_at DESC
        """, (pipeline_id,))

        row = cursor.fetchone()
        conn.close()

        return row.run_id if row else None

    except Exception as e:
        print(f"❌ insert_pipeline_run error: {e}")
        return None


# ==============================================================
# 5. FETCH USER'S PAST RUNS
# Called on dashboard history page after login
# Returns: list of dicts, one per pipeline run
# ==============================================================
def fetch_user_runs(user_id):
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.run_id,
                p.pipeline_id,
                p.status,
                p.positive_count,
                p.neutral_count,
                p.negative_count,
                p.output_blob_name,
                p.created_at,
                p.completed_at,
                f.original_file_name,
                f.file_size_kb,
                f.row_count
            FROM pipeline_runs p
            JOIN files f ON p.file_id = f.file_id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "run_id":             row.run_id,
                "pipeline_id":        row.pipeline_id,
                "status":             row.status,
                "positive_count":     row.positive_count,
                "neutral_count":      row.neutral_count,
                "negative_count":     row.negative_count,
                "output_blob_name":   row.output_blob_name,
                "created_at":         row.created_at,
                "completed_at":       row.completed_at,
                "original_file_name": row.original_file_name,
                "file_size_kb":       row.file_size_kb,
                "row_count":          row.row_count,
            }
            for row in rows
        ]

    except Exception as e:
        print(f"❌ fetch_user_runs error: {e}")
        return []
    

# ==============================================================
# 8. HISTORY FETCHING USER UPLOADS 
# ==============================================================

    
def fetch_user_files(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        f.file_id,
        f.original_file_name,
        f.uploaded_at,
        pr.pipeline_id,
        pr.status,
        pr.positive_count,
        pr.neutral_count,
        pr.negative_count
    FROM files f
    JOIN pipeline_runs pr ON f.file_id = pr.file_id
    WHERE f.user_id = ?
    ORDER BY f.uploaded_at DESC
    """

    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return rows

# ==============================================================
# 6. CREATE SESSION
# ==============================================================
def create_session(user_id):
    try:
        import uuid
        from datetime import timedelta

        conn   = get_connection()
        cursor = conn.cursor()

        # 👇 Check if ANY session exists for this user (active or inactive)
        cursor.execute("""
            SELECT session_id FROM sessions
            WHERE user_id = ?
        """, (user_id,))

        existing = cursor.fetchone()

        if existing:
            # Reactivate existing session + refresh expiry
            expires_at = datetime.utcnow() + timedelta(days=7)
            cursor.execute("""
                UPDATE sessions 
                SET is_active = 1, expires_at = ?
                WHERE user_id = ?
            """, (expires_at, user_id))
            conn.commit()
            conn.close()
            return existing.session_id  # ← same session_id reused

        # No session ever created — make a fresh one
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)

        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, expires_at, is_active)
            VALUES (?, ?, ?, 1)
        """, (session_id, user_id, expires_at))

        conn.commit()
        conn.close()
        return session_id

    except Exception as e:
        print(f"❌ create_session error: {e}")
        return None



# ==============================================================
# 7. VALIDATE SESSION
# ==============================================================
def validate_session(session_id):
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.session_id, s.expires_at, s.is_active,
                   u.user_id, u.username, u.email
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        if not row.is_active:
            return None
        if row.expires_at < datetime.utcnow():
            return None
        return {
            "user_id":    row.user_id,
            "username":   row.username,
            "email":      row.email,
            "session_id": row.session_id
        }
    except Exception as e:
        print(f"❌ validate_session error: {e}")
        return None


# ==============================================================
# 8. INVALIDATE SESSION (LOGOUT)
# ==============================================================
def invalidate_session(session_id):
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions SET is_active = 0
            WHERE session_id = ?
        """, (session_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ invalidate_session error: {e}")
        return False
    
