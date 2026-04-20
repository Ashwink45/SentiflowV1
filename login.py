import streamlit as st
import extra_streamlit_components as stx
from db import register_user, verify_user, create_session, validate_session, invalidate_session, get_connection
import smtplib
from email.mime.text import MIMEText
import os

# ------------------ COOKIE MANAGER ------------------
import streamlit as st
import extra_streamlit_components as stx
import re

def is_valid_username(username):
    return len(username) >= 5 and username.isalnum()

def is_valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"\d", password)
    )

def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager()
    return st.session_state.cookie_manager

# ------------------ SESSION CHECK ------------------
def check_session():
    cookie_manager = get_cookie_manager()
    session_id = cookie_manager.get("session_id")
    if session_id:
        user = validate_session(session_id)
        if user:
            st.session_state.user    = user
            st.session_state.session_id = session_id
            return True
    return False

# ------------------ LOGOUT ------------------
def logout():
    cookie_manager = get_cookie_manager()
    
    # 1. Kill the database session
    if "session_id" in st.session_state:
        invalidate_session(st.session_state.session_id)
        cookie_manager.delete("session_id")
    
    # 2. THE WIPE: Clear all session keys except the technical ones
    for key in list(st.session_state.keys()):
        if key != "cookie_manager": # Keep the tool, delete the data
            del st.session_state[key]

    # 3. Reset to fresh login state
    st.session_state.user = None
    st.session_state.page = "login"
    st.rerun()

# ------------------ CSS ------------------
def inject_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
            background-color: #080b14;
            color: #c8cad8;
        }
        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding: 2rem 3rem; }

        .app-title {
            font-family: 'Syne', sans-serif;
            font-size: 42px;
            font-weight: 800;
            text-align: center;
            background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
        }
        .app-subtitle {
            text-align: center;
            font-size: 14px;
            color: #555b7a;
            margin-bottom: 40px;
        }

        /* Auth card */
        .auth-card {
            background: linear-gradient(145deg, #0e1220, #121829);
            border: 1px solid #1e2340;
            border-radius: 20px;
            padding: 40px;
            max-width: 480px;
            margin: 0 auto;
            box-shadow: 0 8px 40px rgba(0,0,0,0.5);
        }
        .auth-title {
            font-family: 'Syne', sans-serif;
            font-size: 22px;
            font-weight: 700;
            color: #e2e4f0;
            margin-bottom: 6px;
        }
        .auth-subtitle {
            font-size: 13px;
            color: #555b7a;
            margin-bottom: 28px;
        }
        .toggle-link {
            text-align: center;
            font-size: 13px;
            color: #555b7a;
            margin-top: 20px;
        }
        .toggle-link span {
            color: #a78bfa;
            cursor: pointer;
            font-weight: 600;
        }

        /* Inputs */
        .stTextInput > div > div > input {
            background: #080b14 !important;
            border: 1px solid #1e2340 !important;
            border-radius: 10px !important;
            color: #c8cad8 !important;
            padding: 12px 16px !important;
            font-family: 'DM Sans', sans-serif !important;
            font-size: 14px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #a78bfa !important;
            box-shadow: 0 0 0 2px rgba(167,139,250,0.15) !important;
        }
        .stTextInput label {
            color: #8b8fa8 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }

        /* Buttons */
        .stButton > button {
            font-family: 'Syne', sans-serif;
            font-weight: 600;
            border-radius: 10px;
            padding: 12px 24px;
            width: 100%;
            background: linear-gradient(135deg, #7c3aed, #4f46e5);
            color: white !important;
            border: none !important;
            font-size: 15px;
            transition: opacity 0.2s, transform 0.1s;
            margin-top: 8px;
        }
        .stButton > button:hover {
            opacity: 0.88;
            transform: translateY(-1px);
        }

        /* Nav cards */
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 40px;
        }
        .nav-card {
            background: linear-gradient(145deg, #0e1220, #121829);
            border: 1px solid #1e2340;
            border-radius: 20px;
            padding: 32px 24px;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
        }
        .nav-card:hover {
            border-color: #a78bfa;
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(167,139,250,0.15);
        }
        .nav-card .icon {
            font-size: 36px;
            margin-bottom: 16px;
        }
        .nav-card .card-title {
            font-family: 'Syne', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: #e2e4f0;
            margin-bottom: 8px;
        }
        .nav-card .card-desc {
            font-size: 13px;
            color: #555b7a;
            line-height: 1.6;
        }

        /* Welcome header */
        .welcome-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .welcome-name {
            font-family: 'Syne', sans-serif;
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #a78bfa, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .welcome-sub {
            font-size: 14px;
            color: #555b7a;
            margin-bottom: 32px;
        }

        /* Error / success */
        .err-msg {
            background: rgba(255,75,75,0.08);
            border: 1px solid rgba(255,75,75,0.25);
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 13px;
            color: #ff6b6b;
            margin-bottom: 16px;
        }
        .ok-msg {
            background: rgba(52,211,153,0.08);
            border: 1px solid rgba(52,211,153,0.25);
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 13px;
            color: #34d399;
            margin-bottom: 16px;
        }
        </style>
    """, unsafe_allow_html=True)


# ------------------ LOGIN FORM ------------------
def show_login():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Welcome back</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">Sign in to your SentiFlow account</div>', unsafe_allow_html=True)

    username = st.text_input("Username", key="login_username", placeholder="Enter your username")
    password = st.text_input("Password", key="login_password", placeholder="Enter your password", type="password")

    if st.button("Sign In", key="login_btn"):
        if not username or not password:
            st.markdown('<div class="err-msg">Please fill in all fields</div>', unsafe_allow_html=True)
        else:
            user = verify_user(username, password)
            if user:
                if not user["is_verified"]:
                    st.markdown('<div class="err-msg">Please verify your email first</div>', unsafe_allow_html=True)
                else:
                    session_id = create_session(user["user_id"])
                    cookie_manager = get_cookie_manager()
                    cookie_manager.set("session_id", session_id, max_age=604800)

                    for key in list(st.session_state.keys()):
                        if key != "cookie_manager":
                            del st.session_state[key]

                    st.session_state.user       = user
                    st.session_state.session_id = session_id
                    st.session_state.page       = "home"
                    st.rerun()

    st.markdown("""
        <div class="toggle-link">
            Don't have an account?
            <span onclick="window.location.reload()">Register</span>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Create an account →", key="goto_register"):
        st.session_state.auth_mode = "register"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

import smtplib
from email.mime.text import MIMEText

def send_verification_email(email, token):
    # 1. FIX THE LINK: Use your live Render URL instead of localhost
    base_url = os.getenv("APP_URL", "https://sentiflow.onrender.com")
    link = f"{base_url}/?verify_token={token}"

    msg = MIMEText(f"Click this link to verify your account:\n{link}")
    msg['Subject'] = "Verify your account | SentiFlow"
    
    # 2. USE ENV VARS: Pull from Render's environment variables
    sender_email = os.getenv("EMAIL_USER")
    sender_pass = os.getenv("EMAIL_PASS")

    msg['From'] = sender_email
    msg['To'] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_pass)
        server.send_message(msg)
        server.quit()
        print(f"✅ Verification email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ------------------ REGISTER FORM ------------------
def show_register():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Create account</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">Start analysing feedback in seconds</div>', unsafe_allow_html=True)

    username = st.text_input("Username", key="reg_username", placeholder="Choose a username")
    email    = st.text_input("Email",    key="reg_email",    placeholder="your@email.com")
    password = st.text_input("Password", key="reg_password", placeholder="Create a password", type="password")
    confirm  = st.text_input("Confirm password", key="reg_confirm", placeholder="Repeat password", type="password")

    if st.button("Create Account", key="register_btn"):
        if not username or not email or not password or not confirm:
            st.markdown('<div class="err-msg">Please fill in all fields</div>', unsafe_allow_html=True)
        elif password != confirm:
            st.markdown('<div class="err-msg">Passwords do not match</div>', unsafe_allow_html=True)
        elif not is_valid_username(username):
            st.markdown('<div class="err-msg">Username must be at least 5 characters and contain only letters/numbers</div>', unsafe_allow_html=True)

        elif not is_valid_email(email):
            st.markdown('<div class="err-msg">Enter a valid email address</div>', unsafe_allow_html=True)

        elif not is_strong_password(password):
            st.markdown('<div class="err-msg">Password must be 8+ chars, include uppercase, lowercase, and a number</div>', unsafe_allow_html=True)
        else:
            token = register_user(username, email, password)

            if token:
                send_verification_email(email, token)
                st.markdown('<div class="ok-msg">Verification email sent! Please check your inbox.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="err-msg">Username or email already exists</div>', unsafe_allow_html=True)

    if st.button("← Back to login", key="goto_login"):
        st.session_state.auth_mode = "login"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ------------------ HOME / LANDING PAGE ------------------
def show_home():
    user = st.session_state.user

    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f'<div class="welcome-name">Welcome back, {user["username"]} 👋</div>', unsafe_allow_html=True)
        st.markdown('<div class="welcome-sub">What would you like to do today?</div>', unsafe_allow_html=True)
    with col2:
        if st.button("Logout", key="logout_btn"):
            logout()

    # Nav cards
    st.markdown("""
        <div class="nav-grid">
            <div class="nav-card" id="card-upload">
                <div class="icon">📂</div>
                <div class="card-title">Upload Feedback</div>
                <div class="card-desc">Upload a new CSV file and run the sentiment pipeline</div>
            </div>
            <div class="nav-card" id="card-dashboard">
                <div class="icon">📊</div>
                <div class="card-title">Dashboard</div>
                <div class="card-desc">View sentiment charts and insights from your latest run</div>
            </div>
            <div class="nav-card" id="card-history">
                <div class="icon">🕓</div>
                <div class="card-title">Past Runs</div>
                <div class="card-desc">Browse all your previous uploads and their results</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Invisible buttons mapped to cards
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Go to Upload", key="nav_upload"):
            st.session_state.page = "app"
            st.session_state.active_tab = "upload"
            st.rerun()
    with c2:
        if st.button("Go to Dashboard", key="nav_dashboard"):
            st.session_state.page = "app"
            st.session_state.active_tab = "dashboard"
            st.rerun()
    with c3:
        if st.button("View History", key="nav_history"):
            st.session_state.page = "app"
            st.session_state.active_tab = "history"
            st.rerun()



def verify_user_token(token):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM users WHERE verification_token = ?",
        (token,)
    )
    
    row = cursor.fetchone()

    if row:
        user_id = row[0]

        cursor.execute("""
            UPDATE users
            SET is_verified = 1,
                verification_token = NULL
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False

# ------------------ MAIN RENDER ------------------
def render_auth():
    inject_css()

    query_params = st.query_params

    if "verify_token" in query_params:
        token = query_params["verify_token"]

        if verify_user_token(token):
            st.success("✅ Email verified! You can now log in.")
        else:
            st.error("❌ Invalid or expired token")

    st.markdown('<div class="app-title">⚡ SentiFlow</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Sentiment analysis for any feedback CSV</div>', unsafe_allow_html=True)

    # Init state
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "user" not in st.session_state:
        st.session_state.user = None

    # Check existing cookie session
    if st.session_state.user is None:
        check_session()

    # Route
    if st.session_state.user:
        show_home()
    elif st.session_state.auth_mode == "register":
        show_register()
    else:
        show_login()