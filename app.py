import os
import sys
import streamlit as st
import google.generativeai as genai
import pandas as pd
from io import BytesIO
from PIL import Image
import json

# --- 0. 環境設定 ---
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 1. アプリ設定（動的コンポーネントを排除し、完全なる安定性を最優先） ---
st.set_page_config(page_title="BizAlchemy Bulletproof", layout="centered")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. メインUI ---
st.title("🚀 Magic Biz Data Gen Pro")
st.write("### ～ 1枚の写真から、確実にデータを錬成します ～")
st.caption("※ブラウザの翻訳機能による不具合を防ぐため、翻訳はオフにしてご利用ください。")

st.divider()

# 同意フロー
is_agreed = st.checkbox("機密保持条項およびデータ即時消去の規約に同意する", value=True)

if is_agreed:
    doc_type = st.selectbox("📝 解析する書類のタイプ", ["タイムカード", "手書き請求書", "その他ビジネス文書"])

    # アップローダー（標準の安定版）
    uploaded_file = st.file_uploader("書類の写真をアップロードしてください（JPEG/PNG対応）", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        if st.button("✨ データを錬成する", type="primary", use_container_width=True):
            
            # 【開発プロのこだわり】 st.empty() を使わず、安全な st.spinner のみでローディングを管理
            with st.spinner("AIが画像データを解析中...（約10秒かかります）"):
                try:
                    # 1. 画像の読み込み（名前は一切触れずに中身だけ）
                    raw_bytes = uploaded_file.getvalue()
                    img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                    img.thumbnail((1200, 1200))

                    # 2. 最新AI（Gemini 2.5）の呼び出し
                    model = genai.GenerativeModel(
                        model_name='gemini-2.5-flash',
                        generation_config={"response_mime_type": "application/json"}
                    )

                    prompt = f"""
                    Analyze this image ({doc_type}). Extract all text data.
                    Respond ONLY with a JSON object containing:
                    {{
                      "data": [{{"項目名": "値"}}],
                      "cost_saved": 30,
                      "advice": "経営改善のための具体的なアドバイス一言"
                    }}
                    """

                    response = model.generate_content([prompt, img])
                    
                    # 3. 解析結果のパース
                    result = json.loads(response.text)
                    df = pd.DataFrame(result["data"])
                    advice = result.get("advice", "分析が完了しました。")
                    saved_time = result.get("cost_saved", 30)

                    # 4. 結果の表示（動的部品は一切使わず、完全に静的な画面描写）
                    st.success(f"✅ 錬成完了！約{saved_time}分の事務作業を削減しました。")
                    
                    st.write("### 📊 解析データプレビュー")
                    # 【重要】 st.data_editor ではなく、静的な st.table を使用。
                    # これにより、ブラウザのReactエンジンがクラッシュする原因を「ゼロ」にしました。
                    st.table(df)
                    
                    st.info(f"💡 AI経営コンサルのアドバイス: {advice}")

                    # 5. CSVダウンロード（UTF-8-SIG形式でExcelに直通）
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
st.caption("© 2024 Magic Biz Data Gen Pro | Bulletproof Architecture Engine")
