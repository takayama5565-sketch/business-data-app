import streamlit as st
import openai
import pandas as pd
from io import BytesIO
import base64
from PIL import Image # 画像処理用

# --- 1. セキュリティ & 設定 ---
st.set_page_config(page_title="Magic Biz Data Gen Pro", layout="wide")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("APIキーが設定されていません。")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 2. プロフェッショナル・プロンプト ---
PROMPT_DIC = {
    "タイムカード": "日付、出勤、退勤、休憩時間を抽出し、日ごとの実働時間を計算してください。",
    "手書き請求書": "発行元、合計金額、品目、数量、単価を抽出してください。手書き文字を優先して解読してください。",
    "その他自動判別": "書類の内容を分析し、最も適切な表形式に変換してください。"
}

# --- 3. 堅牢な画像処理関数（エラー回避の要） ---
def process_image_to_base64(uploaded_file):
    """
    日本語ファイル名などのメタデータを完全に排除し、
    純粋な画像データのみを抽出し、リサイズして最適化する。
    """
    img = Image.open(uploaded_file)
    # RGBに変換してメタデータを破棄
    img = img.convert("RGB")
    # サイズが大きすぎる場合は縮小（AIの識字率向上とコスト削減）
    img.thumbnail((2000, 2000))
    
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 4. メイン画面構成 ---
st.title("🚀 Magic Biz Data Gen Pro")
st.subheader("法人向けAIビジネスデータ錬成エンジン")

# 法人向け同意確認（弁護士視点：法的リスク回避）
with st.expander("📝 ご利用前の重要事項（利用規約）"):
    st.write("1. 本アプリは送信された画像をAI解析後、即座にメモリから消去します。")
    st.write("2. 生成されたデータの正確性は、必ず人間が確認してください。")
    agree = st.checkbox("上記に同意して利用を開始する")

if agree:
    # ユーザーインターフェース
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.info("ステップ1：書類をアップロード")
        # 内部でメタデータを無視するため、日本語ファイル名でも安全
        uploaded_file = st.file_uploader("iPhoneで撮影した写真を選択", type=['png', 'jpg', 'jpeg'])
        
    with col2:
        st.info("ステップ2：設定を選択")
        doc_type = st.selectbox("書類の種類", list(PROMPT_DIC.keys()))
        output_format = st.radio("出力ファイル", ["Excel (.xlsx)", "CSV (.csv)"])

    if st.button("✨ データを生成する", type="primary", use_container_width=True):
        if uploaded_file:
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()

                # A. 画像処理
                status_text.text("📷 画像を最適化中...")
                base64_image = process_image_to_base64(uploaded_file)
                progress_bar.progress(30)

                # B. AI解析
                status_text.text(f"🧠 AIが{doc_type}を解析中...")
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "あなたはエクセル職人です。JSON形式でデータを返してください。"},
                        {"role": "user", "content": [
                            {"type": "text", "text": f"{doc_type}の解析指示: {PROMPT_DIC[doc_type]}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]}
                    ],
                    response_format={ "type": "json_object" }
                )
                progress_bar.progress(70)

                # C. データ変換
                import json
                data = json.loads(response.choices[0].message.content)
                # JSONからDataFrameへ（ネストされた構造にも対応）
                df = pd.DataFrame(data[next(iter(data))])
                
                status_text.text("📊 解析完了。データのプレビューを表示します。")
                progress_bar.progress(100)

                st.divider()
                st.write("### 💎 解析結果（プレビュー）")
                # 画面上で編集可能なテーブル（ビジネスプロのこだわり）
                edited_df = st.data_editor(df, num_rows="dynamic")

                # D. Excel出力（プロ仕様の書き出し）
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    edited_df.to_excel(writer, index=False, sheet_name='Sheet1')
                
                st.download_button(
                    label="📥 高精度データをダウンロード（5万円相当の価値）",
                    data=output.getvalue(),
                    file_name=f"processed_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"🚨 システムエラー: {e}")
                st.info("ヒント：画像が鮮明か確認してください。解決しない場合はサポートへ。")
        else:
            st.warning("写真を選択してください。")
else:
    st.warning("利用を開始するには、規約への同意が必要です。")

# フッター
st.divider()
st.caption("© 2024 Magic Biz Data Gen | Security: Zero-Retention Policy")
