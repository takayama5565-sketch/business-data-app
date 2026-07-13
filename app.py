import os
import streamlit as st
from google import genai  # 2026年最新のGoogle GenAI SDKを使用します
import pandas as pd
from io import BytesIO
from PIL import Image
import json

# --- 0. 環境設定 ---
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 1. アプリ設定（動的コンポーネントを排除し、安全性を最優先） ---
st.set_page_config(page_title="BizAlchemy Modern Pro", layout="centered")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

# 最新SDKによるクライアント初期化
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. メインUI ---
st.title("🚀 Magic Biz Data Gen Pro")
st.write("### ～ 1枚の写真から、確実にデータを錬成します ～")
st.caption("※2026年最新の『google-genai』システムで正常に起動しています。")

st.divider()

# 同意フロー
is_agreed = st.checkbox("機密保持条項およびデータ即時消去の規約に同意する", value=True)

if is_agreed:
    doc_type = st.selectbox("📝 解析する書類のタイプ", ["タイムカード", "手書き請求書", "その他ビジネス文書"])

    # アップローダー（標準の安定版）
    uploaded_file = st.file_uploader("書類の写真をアップロードしてください（JPEG/PNG対応）", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        if st.button("✨ データを錬成する", type="primary", use_container_width=True):
            
            with st.spinner("最新AIが画像データを解析中...（約10秒かかります）"):
                try:
                    # 1. 画像の読み込み（名前は触れずに中身だけ）
                    raw_bytes = uploaded_file.getvalue()
                    img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                    img.thumbnail((1200, 1200))

                    # 2. 最新AI（Gemini 2.5）への問い合わせ
                    prompt = f"""
                    Analyze this image ({doc_type}). Extract all text data.
                    Respond ONLY with a JSON object containing:
                    {{
                      "data": [{{"項目名": "値"}}],
                      "advice": "経営改善のための具体的なアドバイス一言"
                    }}
                    """

                    # 最新SDK形式の通信
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt, img]
                    )

                    # 3. 解析結果のデコード
                    result = json.loads(response.text)
                    df = pd.DataFrame(result["data"])
                    advice = result.get("advice", "分析が完了しました。")

                    st.success("✅ 錬成完了！")
                    
                    st.write("### 📊 解析データプレビュー")
                    st.table(df) # クラッシュしない静的テーブル
                    
                    st.info(f"💡 AI経営コンサルのアドバイス: {advice}")

                    # 4. CSVダウンロード（UTF-8-SIG形式でExcelに直通）
                    csv_data = df.to_csv(index=False, encoding='utf-8-sig')

                    st.download_button(
                        label="📥 CSVファイル（エクセル対応）を保存する",
                        data=csv_data,
                        file_name="biz_refined_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                except Exception as e:
                    st.error("🚨 処理中にシステムエラーが発生しました。")
                    st.exception(e)
else:
    st.info("同意にチェックを入れると開始できます。")

st.divider()
st.caption("© 2024 Magic Biz Data Gen Pro | Google GenAI SDK Standard")
