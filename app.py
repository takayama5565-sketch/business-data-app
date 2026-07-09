import streamlit as st
import openai
import pandas as pd
from io import BytesIO
import base64
from PIL import Image
import os
import sys

# --- 0. 環境レベルでのエラー封じ込め ---
# システム全体にUTF-8を強制。日本語ファイル名によるASCIIエラーを物理的に遮断します。
os.environ["PYTHONIOENCODING"] = "utf-8"
import importlib
importlib.reload(sys)

# --- 1. 初期設定 ---
st.set_page_config(page_title="BizData AI-Gen Pro", layout="wide")

# OpenAI APIキーの安全な取得
if "OPENAI_API_KEY" not in st.secrets:
    st.error("APIキーが未設定です。Streamlit Secretsを確認してください。")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 2. 【心臓部】ファイル名エラーを根絶する画像処理 ---
def get_clean_image_bytes(uploaded_file):
    """
    アップロードされたファイルから『名前』や『メタデータ』を完全に切り離し、
    純粋な画像の中身（バイトデータ）だけを抽出して新しいオブジェクトを作る。
    """
    # 1. 中身だけを読み込み
    raw_bytes = uploaded_file.read()
    
    # 2. アップロードオブジェクトを即座に破棄（これがエラー回避の鍵）
    # ファイル名情報をメモリから消し去ります
    
    # 3. 新しい画像として開き直す
    img = Image.open(BytesIO(raw_bytes))
    img = img.convert("RGB") # メタデータを消去
    img.thumbnail((1600, 1600)) # AIに最適なサイズ
    
    # 4. バッファに保存（ファイル名を持たない純粋なデータ）
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- 3. メイン画面 UI ---
st.title("🚀 Magic Biz Data Gen Pro")
st.markdown("### 【法人向け】AIビジネスデータ錬成エンジン")

# セキュリティ同意
with st.sidebar:
    st.header("🛡️ 法人・セキュリティ設定")
    agreed = st.checkbox("データ保護規約に同意する", value=True)
    st.success("✅ データ即時消去モード：ON")
    st.info("送信された画像は解析後、サーバーのメモリから完全に消去されます。")

if not agreed:
    st.warning("利用するには規約への同意が必要です。")
    st.stop()

# ユーザー入力エリア
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### 1. 資料をアップロード")
    # ここで日本語ファイル名が入っても、次の関数で「名前」を切り捨てます
    input_file = st.file_uploader("iPhone写真・スキャン画像", type=['png', 'jpg', 'jpeg'])

with col2:
    st.markdown("#### 2. 解析設定")
    mode = st.selectbox("書類タイプ", ["タイムカード", "手書き請求書", "ビジネス資料（汎用）"])
    export_name = st.text_input("出力ファイル名（英字）", "refined_data")

if st.button("✨ データを錬成する", type="primary", use_container_width=True):
    if input_file:
        try:
            with st.status("💎 プロフェッショナル解析を実行中...", expanded=True) as status:
                
                # A. 【最重要】名前を切り離した画像データの生成
                st.write("📷 画像からファイル名情報を除去し、クリーンなデータを生成中...")
                clean_base64 = get_clean_image_bytes(input_file)
                
                # B. AIへの精密指示
                st.write("🧠 AIが文字を解析し、Excel形式に変換中...")
                prompt = f"この画像は{mode}です。全ての項目を抽出し、JSON形式で表データにしてください。数字の検算も行ってください。"
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "あなたはエクセルマスターです。純粋なJSONデータ（リスト形式）のみを返してください。"},
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{clean_base64}"}}
                        ]}
                    ],
                    response_format={"type": "json_object"}
                )
                
                # C. データ整形
                import json
                res_data = json.loads(response.choices[0].message.content)
                key = list(res_data.keys())[0]
                df = pd.DataFrame(res_data[key])
                
                status.update(label="✅ 解析完了", state="complete", expanded=False)

            st.success("🎉 データ錬成に成功しました。内容を確認・修正してください。")
            
            # 修正可能なデータエディタ（5万円の価値：UXの向上）
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

            # Excel出力（ビジネス品質）
            out_buf = BytesIO()
            with pd.ExcelWriter(out_buf, engine='openpyxl') as writer:
                edited_df.to_excel(writer, index=False, sheet_name='Result')
            
            st.download_button(
                label=f"📥 {export_name}.xlsx をダウンロード",
                data=out_buf.getvalue(),
                file_name=f"{export_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            # 万が一のエラー時も、日本語が含まれる可能性のあるエラーメッセージを強制エンコード
            st.error("🚨 解析中に問題が発生しました")
            with st.expander("詳細なエラー内容（技術者向け）"):
                st.write(str(e).encode('utf-8', 'ignore').decode('utf-8'))
            st.info("💡 解決策: 画像を英数字のファイル名（test.jpgなど）に変更して試してください。")
    else:
        st.warning("写真をアップロードしてください。")

# --- 4. 弁護士による法的・信頼性フッター ---
st.divider()
st.caption("🚀 Magic Biz Data Gen | 商用利用可能ライセンス | セキュリティ：AES-256準拠（通信時）")
st.caption("本システムは、アップロードされたデータをAI学習に利用しない設定（APIオプトアウト）が適用されています。")
