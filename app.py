import os
import sys
import locale

# --- 0. 環境設定 ---
try:
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
except:
    pass
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
import google.generativeai as genai
import pandas as pd
from io import BytesIO
from PIL import Image
import json

# --- 1. HEICデコーダー登録 ---
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# --- 2. アプリ設定 ---
st.set_page_config(page_title="BizAlchemy Debug Mode", layout="wide")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_safe_pil_image(uploaded_file):
    try:
        raw_bytes = uploaded_file.getvalue()
        img = Image.open(BytesIO(raw_bytes))
        img = img.convert("RGB")
        img.thumbnail((1200, 1200))
        return img
    except Exception as e:
        st.error(f"画像変換エラー: {e}")
        return None

# --- 3. UI構築 ---
st.title("🚀 BizData Gen Pro - Debug Mode")
st.write("### 現在、詳細なエラー原因を特定するためのデバッグモードで起動しています。")

uploaded_file = st.file_uploader("テスト用写真をアップロードしてください", type=['png', 'jpg', 'jpeg', 'heic', 'HEIC'])

if st.button("✨ テスト解析を実行する", type="primary", use_container_width=True):
    if uploaded_file:
        msg = st.empty()
        try:
            msg.info("📷 画像を変換中...")
            img_obj = get_safe_pil_image(uploaded_file)
            
            if not img_obj:
                st.stop()

            msg.info("🧠 Gemini APIへ通信テスト中...")
            
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                generation_config={"response_mime_type": "application/json"}
            )

            prompt = """
            Analyze this image. Extract all text into a JSON format:
            {"data": [{"item": "text_value"}]}
            """

            # API通信
            response = model.generate_content([prompt, img_obj])
            
            # 結果を表示
            st.success("🎉 通信成功！解析データを受信しました。")
            st.write(response.text)

        except Exception as e:
            # 5万円の価値：原因を隠さず、システムエラーを画面にそのまま綺麗に表示するプロの技術
            msg.error("🚨 解析プロセスでシステムエラーを検出しました。以下の詳細情報をチームに共有してください：")
            st.exception(e) # ここで本当の原因が画面に表示されます
    else:
        st.warning("写真をアップロードしてください。")
