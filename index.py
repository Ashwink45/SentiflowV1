import streamlit as st
import io
import pandas as pd
from PIL import Image
from azure.storage.blob import BlobServiceClient
import uuid
import plotly.graph_objects as go
from collections import Counter
import re
from config import CONN_STR as conn_str
from db import insert_file, insert_pipeline_run


# DIAGNOSTIC PRINT
if not conn_str:
    st.error("❌ Critical Error: Azure Connection String is missing!")
    st.stop()
else:
    # This only prints to logs as a simple confirmation
    print("✅ System: Azure Storage credentials verified.", flush=True)

if conn_str is None:
    st.error("❌ Critical Error: Azure Connection String is missing! Check your .env file.")
    st.stop()

# ------------------ PAGE CONFIG (must be first) ------------------
st.set_page_config(
    page_title="SentiFlow",
    layout="wide",
    page_icon="📊"
)

# ------------------ IMPORTS AFTER PAGE CONFIG ------------------
from clean import process_blob
from login import render_auth
from db import insert_file, insert_pipeline_run, fetch_user_files

# ------------------ SESSION INIT ------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "pipeline_id" not in st.session_state:
    st.session_state.pipeline_id = None

# ------------------ ROUTE ------------------
if st.session_state.page == "login" or st.session_state.user is None:
    render_auth()
    st.stop()

# ------------------ AZURE CONFIG ------------------

def upload_to_blob(uploaded_file):
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    pipeline_id = str(uuid.uuid4())
    blob_name   = f"upload_{pipeline_id}.csv"
    blob_client = blob_service_client.get_blob_client(container="raw-data", blob=blob_name)
    blob_client.upload_blob(uploaded_file, overwrite=True)
    return {"blob_name": blob_name, "pipeline_id": pipeline_id}

# ------------------ GLOBAL CSS ------------------
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
        letter-spacing: -1px;
        background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .app-subtitle {
        text-align: center;
        font-size: 15px;
        color: #555b7a;
        margin-bottom: 32px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #0e1220;
        border-radius: 12px;
        padding: 6px;
        border: 1px solid #1e2340;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Syne', sans-serif;
        font-size: 15px;
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 24px;
        color: #555b7a;
        background: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e2a4a, #1a2540) !important;
        color: #a78bfa !important;
        border: 1px solid #2e3a6e !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"]    { display: none; }

    .upload-card {
        background: linear-gradient(145deg, #0e1220, #121829);
        border: 1px solid #1e2340;
        border-radius: 20px;
        padding: 40px;
        margin-top: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    [data-testid="stFileUploader"] {
        background: #080b14;
        border: 2px dashed #2e3a6e;
        border-radius: 14px;
        padding: 20px;
    }
    .stButton > button, .stDownloadButton > button {
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        border-radius: 10px;
        padding: 10px 24px;
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: white;
        border: none;
        transition: opacity 0.2s, transform 0.1s;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        opacity: 0.88;
        transform: translateY(-1px);
    }
    .stSelectbox > div > div,
    .stTextInput > div > div > input {
        background: #0e1220 !important;
        border: 1px solid #1e2340 !important;
        border-radius: 10px !important;
        color: #c8cad8 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .metric-card {
        background: linear-gradient(145deg, #0e1220, #121829);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #1e2340;
        text-align: center;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); border-color: #2e3a6e; }
    .metric-value {
        font-family: 'Syne', sans-serif;
        font-size: 38px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -1px;
    }
    .metric-label {
        font-size: 11px;
        color: #555b7a;
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 500;
    }
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 17px;
        font-weight: 700;
        color: #e2e4f0;
        margin: 40px 0 16px 0;
        padding-bottom: 10px;
        border-bottom: 1px solid #1e2340;
    }
    .keyword-chip {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 4px;
    }
    .neg-chip { background: rgba(255,107,107,0.1); color: #ff6b6b; border: 1px solid rgba(255,107,107,0.25); }
    .pos-chip { background: rgba(52,211,153,0.1);  color: #34d399; border: 1px solid rgba(52,211,153,0.25); }
    .neu-chip { background: rgba(251,191,36,0.1);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.25); }
    .feedback-card {
        background: linear-gradient(145deg, #0e1220, #0a0f1c);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 10px;
        border-left: 3px solid;
        font-size: 14px;
        color: #9ca3b8;
        line-height: 1.7;
        transition: background 0.2s;
    }
    .feedback-card:hover { background: #121829; }
    .feedback-neg { border-left-color: #ff6b6b; }
    .feedback-pos { border-left-color: #34d399; }
    .feedback-neu { border-left-color: #fbbf24; }
    .feedback-badge {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 6px;
    }
    .empty-state { text-align: center; padding: 100px 0; color: #555b7a; }
    .empty-icon  { font-size: 52px; margin-bottom: 16px; }
    .empty-title { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: #3a4060; }
    .empty-sub   { font-size: 14px; margin-top: 8px; }
    .user-badge  { text-align: right; font-size: 13px; color: #555b7a; margin-bottom: 8px; }
    .user-badge span { color: #a78bfa; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
user = st.session_state.user

col_title, col_user = st.columns([5, 1])
with col_title:
    st.markdown('<div class="app-title">⚡ SentiFlow</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Upload any feedback CSV — get instant sentiment analysis</div>', unsafe_allow_html=True)
with col_user:
    st.markdown(f'<div class="user-badge">Signed in as <span>{user["username"]}</span></div>', unsafe_allow_html=True)
    if st.button("Logout", key="logout_btn"):
        from login import logout
        logout()

# ------------------ TABS ------------------
tab1, tab2, tab3 = st.tabs(["📂  Upload", "⚙️  Pipeline", "📊  Dashboard"])

# ══════════════════════════════════════════
# TAB 1 — UPLOAD
# ══════════════════════════════════════════
with tab1:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload your feedback CSV", type=["csv"])

    if uploaded_file:
        st.info(f"📄 File '{uploaded_file.name}' ready for processing.")
        
        # 🟢 NEW BUTTON GATE: Only runs when you click this
        if st.button("🚀 Start the Analysis", key="start_analysis_btn"):
            
            # 1 — Upload to raw-data blob
            with st.spinner("Uploading to Azure..."):
                upload_result = upload_to_blob(uploaded_file)
                blob_name = upload_result["blob_name"]
                pipeline_id = upload_result["pipeline_id"]
            
            # 2 — Clean + trigger ML
            with st.spinner("Running pipeline: cleaning → sentiment analysis ⏳"):
                # We call the ML trigger ONLY once here
                result = process_blob(blob_name, pipeline_id)

            st.success("✅ Pipeline complete! Your results are ready.")

            # 3 — Update session state (This tells Tab 3 which data to show)
            st.session_state.pipeline_id = pipeline_id

            # 4 — Fetch results from output-data to save metadata
            output_blob_name = f"output_{pipeline_id}.csv"
            blob_service_client = BlobServiceClient.from_connection_string(conn_str)
            blob_client = blob_service_client.get_blob_client(container="output-data", blob=output_blob_name)

            try:
                # Wait a moment if needed, then download
                output_data = blob_client.download_blob().readall()
                df_output = pd.read_csv(io.BytesIO(output_data))

                pos_count = int(len(df_output[df_output["Sentiment"] == "Positive"]))
                neu_count = int(len(df_output[df_output["Sentiment"] == "Neutral"]))
                neg_count = int(len(df_output[df_output["Sentiment"] == "Negative"]))
                row_count = int(len(df_output))

                # 5 — Write metadata to Azure SQL
                try:
                    file_id = insert_file(
                        user_id = user["user_id"],
                        original_file_name = uploaded_file.name,
                        file_size_kb = round(uploaded_file.size / 1024, 2),
                        row_count = row_count,
                        raw_blob_name = blob_name
                    )
                    insert_pipeline_run(
                        file_id = file_id,
                        user_id = user["user_id"],
                        pipeline_id = pipeline_id,
                        positive_count = pos_count,
                        neutral_count = neu_count,
                        negative_count = neg_count,
                        output_blob_name = output_blob_name
                    )
                    st.success("✅ Results archived in database.")
                except Exception as e:
                    st.warning(f"⚠️ Metadata save failed: {e}")

                # 6 — Immediate download option
                st.download_button(
                    label = "⬇️ Download Analyzed CSV",
                    data = output_data,
                    file_name = f"analyzed_{uploaded_file.name}",
                    mime = "text/csv"
                )

            except Exception as e:
                st.error(f"❌ Pipeline finished but results weren't found in Azure: {e}")
    else:
        st.info("📁 No file uploaded yet. Choose a CSV file above to begin.")

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 2 — PIPELINE INFO
# ══════════════════════════════════════════
with tab2:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📂 My Uploads</div>', unsafe_allow_html=True)

    user_id = user["user_id"]

    try:
        files = fetch_user_files(user_id)

        if not files:
            st.markdown("""
                <div class="empty-state">
                    <div class="empty-icon">📁</div>
                    <div class="empty-title">No uploads yet</div>
                    <div class="empty-sub">Upload a CSV to see it here</div>
                </div>
            """, unsafe_allow_html=True)

        else:
            for row in files:
                file_id = row.file_id
                file_name = row.original_file_name
                uploaded_at = row.uploaded_at
                pipeline_id = row.pipeline_id
                status = row.status

                pos = row.positive_count or 0
                neu = row.neutral_count or 0
                neg = row.negative_count or 0

                total = pos + neu + neg
                pos_pct = round((pos/total)*100,1) if total else 0
                neu_pct = round((neu/total)*100,1) if total else 0
                neg_pct = round((neg/total)*100,1) if total else 0

                st.markdown(f"""
                    <div class="feedback-card">
                        <b>📄 {file_name}</b><br>
                        <small style="color:#555b7a;">Uploaded: {uploaded_at}</small><br><br>
                        🟢 {pos_pct}% &nbsp;&nbsp;
                        🟡 {neu_pct}% &nbsp;&nbsp;
                        🔴 {neg_pct}%
                    </div>
                """, unsafe_allow_html=True)

                # BUTTON LOGIC
                if status == "completed":
                    if st.button("View Dashboard", key=f"view_{file_id}"):
                        st.session_state.pipeline_id = pipeline_id
                        st.success("Loaded previous result! Go to Dashboard tab.")

                elif status == "processing":
                    st.info("⏳ Processing...")

                elif status == "failed":
                    st.error("❌ Failed")

                st.markdown("<br>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading history: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 3 — DASHBOARD
# ══════════════════════════════════════════
with tab3:

    # TEMPORARY TEST INPUT — remove after history page is built
    test_id = st.text_input("Test with existing pipeline_id", placeholder="paste pipeline_id here")
    if test_id:
        st.session_state.pipeline_id = test_id

    if not st.session_state.pipeline_id:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <div class="empty-title">No data yet</div>
                <div class="empty-sub">Upload a CSV in the Upload tab to see your dashboard</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        try:
            pipeline_id      = st.session_state.pipeline_id
            output_blob_name = f"output_{pipeline_id}.csv"

            blob_service_client = BlobServiceClient.from_connection_string(conn_str)
            blob_client = blob_service_client.get_blob_client(container="output-data", blob=output_blob_name)
            data   = blob_client.download_blob().readall()
            df_out = pd.read_csv(io.BytesIO(data))

            # counts
            total     = len(df_out)
            pos_count = len(df_out[df_out["Sentiment"] == "Positive"])
            neu_count = len(df_out[df_out["Sentiment"] == "Neutral"])
            neg_count = len(df_out[df_out["Sentiment"] == "Negative"])
            pos_pct   = round((pos_count / total) * 100, 1)
            neu_pct   = round((neu_count / total) * 100, 1)
            neg_pct   = round((neg_count / total) * 100, 1)

            # overview cards
            st.markdown('<div class="section-title">📈 Overview</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            for col, value, label, color in [
                (c1, total,         "Total Feedbacks", "#a78bfa"),
                (c2, f"{pos_pct}%", "Positive",        "#34d399"),
                (c3, f"{neu_pct}%", "Neutral",         "#fbbf24"),
                (c4, f"{neg_pct}%", "Negative",        "#ff6b6b"),
            ]:
                with col:
                    st.markdown(f"""
                        <div class="metric-card">
                            <p class="metric-value" style="color:{color};">{value}</p>
                            <p class="metric-label">{label}</p>
                        </div>
                    """, unsafe_allow_html=True)

            # charts
            st.markdown('<div class="section-title">📊 Sentiment Breakdown</div>', unsafe_allow_html=True)
            col_left, col_right = st.columns(2)
            colors   = ["#34d399", "#fbbf24", "#ff6b6b"]
            chart_bg = "rgba(0,0,0,0)"
            font_clr = "#9ca3b8"

            with col_left:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=["Positive", "Neutral", "Negative"],
                    values=[pos_count, neu_count, neg_count],
                    hole=0.55,
                    marker=dict(colors=colors, line=dict(color="#080b14", width=3)),
                    textinfo="percent+label",
                    textfont=dict(size=13),
                )])
                fig_pie.update_layout(
                    paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                    font=dict(color=font_clr), showlegend=False,
                    margin=dict(t=20, b=20, l=20, r=20), height=300
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_right:
                fig_bar = go.Figure(data=[go.Bar(
                    x=["Positive", "Neutral", "Negative"],
                    y=[pos_count, neu_count, neg_count],
                    marker_color=colors,
                    marker_line=dict(width=0),
                    text=[pos_count, neu_count, neg_count],
                    textposition="auto",
                    textfont=dict(size=13),
                )])
                fig_bar.update_layout(
                    paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                    font=dict(color=font_clr),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="#1e2340"),
                    bargap=0.35,
                    margin=dict(t=20, b=20, l=20, r=20), height=300
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # keywords
            st.markdown('<div class="section-title">🔍 Distinctive Keywords</div>', unsafe_allow_html=True)

            stopwords = set([
                "the","a","an","and","or","but","in","on","at","to","for",
                "of","is","it","this","that","was","with","as","be","are",
                "i","my","we","you","they","he","she","its","our","your",
                "have","has","had","do","did","not","no","so","if","from",
                "by","about","just","been","will","can","all","also","more",
                "their","there","would","could","should","what","which","who",
                "very","get","got","us","me","him","her","them","than","then",
                "when","where","how","up","out","one","two","like","know",
                "university","uni","students","student","campus","course",
                "courses","college","good","great","really","place","overall",
                "feel","felt","think","lot","bit","things","thing","way",
                "make","made","need","needs","even","still","well","said",
                "say","come","came","go","goes","going","many","most","new",
                "old","big","small","long","first","last","year","years",
                "some","only","time","much","don","doesn","didn","isn","aren",
                "wasn","weren","won","couldn","wouldn","shouldn"
            ])

            def get_top_words(dataframe, sentiment, n=15):
                texts = dataframe[dataframe["Sentiment"] == sentiment]["Feedback"].astype(str)
                words = []
                for text in texts:
                    text = re.sub(r"'s|'t|'re|'ve|'ll|'d|n't", "", text.lower())
                    tokens = re.findall(r'\b[a-zA-Z]{4,}\b', text)
                    words.extend([w for w in tokens if w not in stopwords])
                other_top = set(
                    w for s in ["Positive", "Neutral", "Negative"] if s != sentiment
                    for w, _ in Counter(
                        re.findall(r'\b[a-zA-Z]{4,}\b',
                        " ".join(dataframe[dataframe["Sentiment"] == s]["Feedback"].astype(str)).lower())
                    ).most_common(50)
                )
                words = [w for w in words if w not in other_top]
                return Counter(words).most_common(n)

            kw_col1, kw_col2, kw_col3 = st.columns(3)
            for col, sentiment, chip_class, label in [
                (kw_col1, "Positive", "pos-chip", "🟢 Positive Keywords"),
                (kw_col2, "Neutral",  "neu-chip", "🟡 Neutral Keywords"),
                (kw_col3, "Negative", "neg-chip", "🔴 Negative Keywords"),
            ]:
                with col:
                    st.markdown(f"**{label}**")
                    top_words = get_top_words(df_out, sentiment)
                    if top_words:
                        chips = " ".join([
                            f'<span class="keyword-chip {chip_class}">{w} <small>({c})</small></span>'
                            for w, c in top_words
                        ])
                        st.markdown(chips, unsafe_allow_html=True)
                    else:
                        st.markdown("<small style='color:#555b7a;'>No distinctive keywords found</small>", unsafe_allow_html=True)

            # feedback explorer
            st.markdown('<div class="section-title">💬 Feedback Explorer</div>', unsafe_allow_html=True)
            filter_col, search_col = st.columns([2, 4])
            with filter_col:
                filter_option = st.selectbox("Filter by Sentiment", ["All", "Positive", "Neutral", "Negative"])
            with search_col:
                search_term = st.text_input("🔎 Search feedback", placeholder="Type to search...")

            df_filtered = df_out.copy()
            if filter_option != "All":
                df_filtered = df_filtered[df_filtered["Sentiment"] == filter_option]
            if search_term:
                df_filtered = df_filtered[df_filtered["Feedback"].str.contains(search_term, case=False, na=False)]

            st.markdown(f"<small style='color:#555b7a; letter-spacing:1px;'>SHOWING {len(df_filtered)} RESULTS</small>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            color_map = {"Positive": "#34d399", "Neutral": "#fbbf24", "Negative": "#ff6b6b"}
            class_map = {"Positive": "feedback-pos", "Neutral": "feedback-neu", "Negative": "feedback-neg"}

            for _, row in df_filtered.head(20).iterrows():
                sentiment   = row["Sentiment"]
                badge_color = color_map.get(sentiment, "#9ca3b8")
                css_class   = class_map.get(sentiment, "")
                st.markdown(f"""
                    <div class="feedback-card {css_class}">
                        <div class="feedback-badge" style="color:{badge_color};">{sentiment}</div>
                        <div>{row['Feedback']}</div>
                    </div>
                """, unsafe_allow_html=True)

            # export
            st.markdown('<div class="section-title">⬇️ Export</div>', unsafe_allow_html=True)
            st.download_button(
                label     = "Download Full Output CSV",
                data      = data,
                file_name = output_blob_name,
                mime      = "text/csv"
            )

        except Exception as e:
            st.error(f"❌ Could not load dashboard: {e}")