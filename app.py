import os
import sys
import streamlit as st
from google import genai  # 最新のGoogle GenAI SDK
import pandas as pd
from io import BytesIO
from PIL import Image
import json

# --- 0. 環境設定 ---
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 1. アプリ設定 ---
st.set_page_config(page_title="BizAlchemy Elite Table", layout="centered")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

# 最新SDKクライアント初期化
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# AIの飾り枠を取り除くお掃除フィルター
def clean_json_string(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

# --- 2. メインUI ---
st.title("🚀 Magic Biz Data Gen Pro")
st.write("### ～ 1枚の写真から、エクセル形式の表を錬成します ～")

st.divider()

is_agreed = st.checkbox("機密保持条項およびデータ即時消去の規約に同意する", value=True)

if is_agreed:
    doc_type = st.selectbox("📝 解析する書類のタイプ", ["タイムカード", "手書き請求書", "その他ビジネス文書"])
    uploaded_file = st.file_uploader("書類の写真をアップロードしてください（JPEG/PNG対応）", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        if st.button("✨ データを錬成する", type="primary", use_container_width=True):
            with st.spinner("AIが画像データを解析中...（約10秒かかります）"):
                try:
                    # 1. 画像の読み込み
                    raw_bytes = uploaded_file.getvalue()
                    img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                    img.thumbnail((1200, 1200))

                    # 2. 【プロ設計】横一列の表形式をAIに強制するプロンプト
                    prompt = f"""
                    Analyze this image ({doc_type}). Extract the timecard data.
                    You must structure the output as a horizontal database table.
                    Format your response ONLY as a JSON object containing a "data" list.
                    
                    Each item in the "data" list must represent one day's row, with these exact columns:
                    - "氏名" (Extra
