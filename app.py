import os
import sys
import streamlit as st
from google import genai  # 2026年最新のSDK
import pandas as pd
from io import BytesIO
from PIL import Image
import json

# --- 0. 環境設定 ---
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 1. アプリ設定（完全なる安定性を最優先） ---
st.set_page_config(page_title="BizAlchemy Bulletproof Pro", layout="centered")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

# 最新SDKクライアント初期化
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. 5万円の価値：AIの余計な飾り文字を綺麗に掃除するフィルター ---
def clean_json_string(text):
    """
    AIが返事の前後につけてしまう ```json などの飾り枠を
    物理的に切り落とし、純粋なデータだけにするお掃除関数。
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

# --- 3. メインUI ---
st.title("🚀 Magic Biz Data Gen Pro")
st.write("### ～ 1枚の写真から、確実にデータをCSVに変換します ～")
st.caption("※2026年最新の『google-genai』システムで起動しています。")

st.divider()

is_agreed = st.checkbox("機密保持条項およびデータ即時消去の規約に同意する", value=True)

if is_agreed:
    doc_type = st.selectbox("📝 解析する書類のタイプ", ["タイムカード", "手書き請求書", "その他ビジネス文書"])
    uploaded_file = st.file_uploader("書類の写真をアップロードしてください（JPEG/PNG対応）", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        if st.button("✨ データを錬成する", type="primary", use_container_width=True):
            with st.spinner("最新AIが画像データを解析中...（約10秒かかります）"):
                try:
                    # 1. 画像の読み込み
                    raw_bytes = uploaded_file.getvalue()
                    img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                    img.thumbnail((1200, 1200))

                    # 2. プロンプト（指示書）
                    prompt = f"""
                    Analyze this image ({doc_type}). Extract all text data.
                    Respond ONLY with a JSON object containing:
                    {{
                      "data": [{{"項目名": "値"}}],
                      "advice": "経営改善のための具体的なアドバイス一言"
                    }}
                    """

                    # 3. API通信（辞書型設定で、AIにおしゃべりを禁止しJSONでの返答を強制）
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt, img],
                        config={
                            "response_mime_type": "application/json"
                        }
                    )

                    # 4. 安全なパース処理（お掃除フィルター適用）
                    raw_text = response.text
                    cleaned_text = clean_json_string(raw_text)
                    
                    try:
                        result = json.loads(cleaned_text)
                        df = pd.DataFrame(result["data"])
                        advice = result.get("advice", "分析が完了しました。")
                    except json.JSONDecodeError:
                        # 【5万円の価値：フォールバック】
                        # 万が一データ化に失敗しても、画面をクラッシュさせずに生のAIテキストを表示して救うプロの技術
                        st.warning("⚠️ データの自動表作成に失敗しました。解析された生データを表示します。")
                        st.text_area("AIの生データ", raw_text, height=300)
                        st.stop()

                    st.success("✅ 錬成完了！")
                    
                    st.write("### 📊 解析データプレビュー")
                    st.table(df) # 100%安全な静的テーブル
                    
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
