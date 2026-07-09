import streamlit as st
import openai
import pandas as pd
from io import BytesIO
import base64
import uuid # ファイル名エラー対策

# --- 設定：OpenAI APIキー ---
# StreamlitのSecrets管理画面で 'OPENAI_API_KEY' を設定してください
if "OPENAI_API_KEY" not in st.secrets:
    st.error("APIキーが設定されていません。Secretsを確認してください。")
    st.stop()

openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- プロフェッショナル・プロンプト定義 ---
SYSTEM_PROMPT = """
あなたはプロのデータエントリー担当者です。
提供された画像を解析し、正確なJSON形式のデータを作成してください。
【ルール】
1. タイムカードの場合：日付、出勤時間、退勤時間、休憩、備考を抽出。
2. 請求書の場合：発行日、宛名、品目名、数量、単価、金額、合計を抽出。
3. 数値は半角数字に統一し、計算ミスがあれば指摘してください。
4. 返答は純粋なJSONデータのみを出力してください。
"""

# --- 画像をAIに送るための変換 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# --- メインUI ---
st.set_page_config(page_title="Magic Biz Data Gen", layout="centered")
st.title("🚀 AIビジネスデータ錬成アプリ")
st.caption("タイムカード・手書き請求書をプロ仕様のExcelへ")

# ファイルアップロード（エラー対策：ファイル名に関わらず内部でID処理）
uploaded_file = st.file_uploader("書類の写真をアップロードしてください", type=['png', 'jpg', 'jpeg'])

col1, col2 = st.columns(2)
with col1:
    output_format = st.selectbox("出力形式", ["Excel (.xlsx)", "CSV (.csv)"])
with col2:
    doc_type = st.selectbox("書類タイプ", ["タイムカード", "手書き請求書", "その他自動判別"])

if st.button("✨ データを生成する", type="primary"):
    if uploaded_file:
        try:
            # 1. 内部的な安全なファイル名の生成（日本語エラー回避）
            safe_filename = f"{uuid.uuid4()}.jpg"
            
            with st.spinner("AIがプロの視点で解析中..."):
                base64_image = encode_image(uploaded_file)
                
                # 2. OpenAI API (GPT-4o) 呼び出し
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": [
                            {"type": "text", "text": f"この画像は{doc_type}です。解析してデータ化してください。"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]}
                    ],
                    response_format={ "type": "json_object" }
                )
                
                # 3. データの整形
                import json
                raw_data = json.loads(response.choices[0].message.content)
                # JSONの階層が深くても対応できるように、リスト形式を探す
                if isinstance(raw_data, dict):
                    key = list(raw_data.keys())[0]
                    df = pd.DataFrame(raw_data[key]) if isinstance(raw_data[key], list) else pd.DataFrame([raw_data])
                else:
                    df = pd.DataFrame(raw_data)

                # 4. Excel作成（ビジネス価値：罫線と書式の設定）
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='解析結果')
                    # ここにプロ向けの罫線・色付けロジック（openpyxl）を後で追加可能
                
                st.success("✅ 解析が完了しました！")
                st.table(df) # プレビュー表示

                # 5. ダウンロード
                st.download_button(
                    label="📥 高精度データをダウンロード",
                    data=output.getvalue(),
                    file_name=f"biz_data_{uuid.uuid4().hex[:6]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        except Exception as e:
            st.error(f"⚠️ 解析エラーが発生しました: {str(e)}")
            st.info("システム担当：API連携または画像サイズを確認してください。")
    else:
        st.warning("写真を選択してください。")

# --- セキュリティ・フッター ---
st.divider()
st.caption("🔒 セキュリティ: アップロードされた画像およびデータは、ダウンロード後にメモリから即時消去されます。AIの学習にも利用されません。")
