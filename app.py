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

# --- 1. アプリ設定（安全モード） ---
st.set_page_config(page_title="BizAlchemy Recovery", layout="centered")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.title("🚀 Magic Biz Data Gen - Safe Mode")
st.write("### システムは安全モードで100%復旧しました。URLは正常に稼働しています。")
st.caption("※現在、サーバーの負担を減らすためExcel出力に特化して稼働しています。")

st.divider()

uploaded_file = st.file_uploader("書類をアップロードしてください（JPEG/PNG対応）", type=['png', 'jpg', 'jpeg'])

if st.button("✨ データを錬成する", type="primary", use_container_width=True):
    if uploaded_file:
        msg = st.empty()
        try:
            msg.info("📷 画像データを読み込み中...")
            img_bytes = uploaded_file.getvalue()
            img = Image.open(BytesIO(img_bytes))
            img = img.convert("RGB")
            
            msg.info("🧠 最新AI（Gemini 2.5）が超高速で解析中...")
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                generation_config={"response_mime_type": "application/json"}
            )
            
            prompt = """
            Analyze this image. Extract data into JSON format:
            {
              "data": [{"項目名": "値"}],
              "advice": "経営アドバイス一言"
            }
            """
            
            response = model.generate_content([prompt, img])
            res = json.loads(response.text)
            df = pd.DataFrame(res["data"])
            
            msg.success("✅ 錬成完了！")
            
            st.write("### 📊 解析結果")
            st.dataframe(df, use_container_width=True)
            
            # アドバイスの表示
            st.info(f"💡 AIアドバイス: {res.get('advice', '-')}")
            
            # Excel書き出し
            out_buf = BytesIO()
            with pd.ExcelWriter(out_buf, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
                
            st.download_button(
                label="📥 Excelを保存する",
                data=out_buf.getvalue(),
                file_name="biz_refined_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        except Exception as e:
            msg.error("🚨 処理中にエラーが発生しました。")
            st.exception(e)
    else:
        st.warning("ファイルを選択してください。")

st.divider()
st.caption("© 2024 Magic Biz Data Gen | Safe Recovery System Enabled")
