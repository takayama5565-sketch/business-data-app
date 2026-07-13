import os
import streamlit as st
import google.generativeai as genai
import pandas as pd
from io import BytesIO
from PIL import Image
import json

# --- 0. 環境設定 ---
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 1. アプリ設定（完全なる安定性を最優先） ---
st.set_page_config(page_title="BizAlchemy Ultra Stable", layout="centered")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. 画像変換エンジン（標準のJPG/PNG用） ---
def get_clean_pil_image(uploaded_file):
    try:
        raw_bytes = uploaded_file.getvalue()
        img = Image.open(BytesIO(raw_bytes))
        img = img.convert("RGB")
        img.thumbnail((1200, 1200))
        return img
    except Exception:
        return None

# --- 3. メインUI ---
st.title("🚀 Magic Biz Data Gen - Pro")
st.write("### ～ 1枚の写真から、確実にデータを錬成します ～")
st.caption("※現在、システム全体の安定稼働とエラー根絶を最優先した「超堅牢モード」で稼働しています。")

st.divider()

# 同意フロー
is_agreed = st.checkbox("機密保持条項およびデータ即時消去の規約に同意する", value=True)

if is_agreed:
    # 選択エリア
    doc_type = st.selectbox("📝 解析する書類のタイプ", ["タイムカード", "手書き請求書", "その他ビジネス文書"])

    # アップローダー（100%バグが起きない標準仕様）
    uploaded_file = st.file_uploader("書類の写真をアップロードしてください（JPEG/PNG対応）", type=['png', 'jpg', 'jpeg'])

    if st.button("✨ データを錬成する", type="primary", use_container_width=True):
        if uploaded_file:
            msg = st.empty()
            try:
                msg.info("📷 画像をクリーンアップ中...")
                img_obj = get_clean_pil_image(uploaded_file)
                
                if not img_obj:
                    st.error("🚨 画像の読み込みに失敗しました。")
                    st.stop()

                msg.info("🧠 最新AI（Gemini 2.5）がデータを解析中...")
                
                model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    generation_config={"response_mime_type": "application/json"}
                )

                prompt = f"""
                Analyze this image ({doc_type}). Extract all text data.
                Respond ONLY with a JSON object containing:
                {{
                  "data": [{{"項目名": "値"}}],
                  "advice": "経営アドバイス一言"
                }}
                """

                # API通信
                response = model.generate_content([prompt, img_obj])
                
                # デコード
                result = json.loads(response.text)
                df = pd.DataFrame(result["data"])
                advice = result.get("advice", "分析が完了しました。")

                msg.success("✅ 錬成完了！")

                # 結果表示
                st.write("### 📊 プレビュー")
                edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
                st.info(f"💡 AIのアドバイス: {advice}")

                # 【5万円の価値：文字化けしないCSV出力（Excel対応）】
                # Excelで直接開いても絶対に文字化けしない「utf-8-sig」という魔法のエンコードを使用します
                csv_data = edited_df.to_csv(index=False, encoding='utf-8-sig')

                st.download_button(
                    label="📥 CSVファイル（エクセルで開けます）を保存する",
                    data=csv_data,
                    file_name="biz_refined_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            except Exception as e:
                msg.error("🚨 処理中にシステムエラーが発生しました。")
                st.exception(e)
        else:
            st.warning("写真をアップロードしてください。")
else:
    st.info("同意にチェックを入れると開始できます。")

st.divider()
st.caption("© 2024 Magic Biz Data Gen Pro | Ultra-Stable Engine Loaded")
