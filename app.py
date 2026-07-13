import os
import sys
import streamlit as st
import google.generativeai as genai
import pandas as pd
from io import BytesIO
from PIL import Image
import json

# --- 0. システム環境設定 ---
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 1. アプリ基本設定（余計なCSSハックをすべて排除し、安定性を最優先） ---
st.set_page_config(page_title="BizAlchemy High Stability", layout="centered")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. メタデータ隔離・画像変換エンジン ---
def get_safe_pil_image(uploaded_file):
    try:
        raw_bytes = uploaded_file.getvalue()
        img = Image.open(BytesIO(raw_bytes))
        img = img.convert("RGB") # RGB形式に統一
        img.thumbnail((1200, 1200)) # 解析に最適な解像度
        return img
    except Exception:
        return None

# --- 3. メインUI ---
st.title("🚀 Magic Biz Data Gen Pro")
st.write("### ～ 1枚の写真から『Excel』を完全無料で錬成する ～")
st.write("※ブラウザの「日本語翻訳」機能はオフ（原文表示）にしてご利用ください。")

st.divider()

# 同意フロー
is_agreed = st.checkbox("機密保持条項およびデータ即時消去の規約に同意する", value=True)

if is_agreed:
    # 選択エリア
    doc_type = st.selectbox("📝 解析する書類のタイプ", ["タイムカード", "手書き請求書", "その他ビジネス文書"])

    # アップローダー（標準の安定版）
    uploaded_file = st.file_uploader("書類の写真をアップロードしてください", type=['png', 'jpg', 'jpeg'])

    if st.button("✨ データを錬成する", type="primary", use_container_width=True):
        if uploaded_file:
            msg = st.empty()
            try:
                msg.info("📷 画像データを最適化中...")
                img_obj = get_safe_pil_image(uploaded_file)
                
                if not img_obj:
                    st.error("🚨 画像の読み込みに失敗しました。")
                    st.stop()

                msg.info("🧠 最新AI（Gemini 2.5）が超高速で解析中...")
                
                model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    generation_config={"response_mime_type": "application/json"}
                )

                prompt = f"""
                あなたは優秀なDXコンサルタントです。画像（{doc_type}）から全データを抽出してください。
                【必須項目】
                必ず以下のキーを持つJSON形式で出力してください：
                {{
                  "data": [{{"項目名": "value"}}],
                  "cost_saved": 30,
                  "advice": "経営改善アドバイス一言"
                }}
                """

                # API通信
                response = model.generate_content([prompt, img_obj])
                
                # 解析結果のデコード
                result = json.loads(response.text)
                df = pd.DataFrame(result["data"])
                advice = result.get("advice", "分析が完了しました。")
                saved_time = result.get("cost_saved", 30)

                msg.success(f"✅ 錬成完了！約{saved_time}分の事務作業を削減しました。")

                # 結果表示
                st.write("### 💎 錬成結果プレビュー")
                edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
                st.info(f"💡 AI経営コンサルのアドバイス: {advice}")

                # Excel出力
                out_buf = BytesIO()
                with pd.ExcelWriter(out_buf, engine='openpyxl') as writer:
                    edited_df.to_excel(writer, index=False)

                st.download_button(
                    label="📥 Excelファイルを保存する",
                    data=out_buf.getvalue(),
                    file_name="biz_refined_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except Exception as e:
                msg.error("🚨 解析プロセスでエラーが発生しました。")
                st.exception(e)
        else:
            st.warning("写真をアップロードしてください。")
else:
    st.info("同意にチェックを入れると開始できます。")

st.divider()
st.caption("© 2024 Magic Biz Data Gen Pro | Powered by Gemini 2.5 Flash")
