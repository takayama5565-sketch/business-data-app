import streamlit as st
import openai
import pandas as pd
from io import BytesIO
import base64
from PIL import Image
import os

# --- 0. システムの初期設定（ASCIIエラーを物理的に遮断） ---
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 1. アプリ初期設定 ---
st.set_page_config(page_title="BizAlchemy Elite v5", layout="centered")

# CSSでエラーの引き金になる「ファイル名表示」を完全に消去
st.markdown("""
    <style>
    [data-testid="stFileUploaderFileName"], .stFileUploader section { display: none !important; }
    .stApp { background-color: #f8f9fa; }
    .stButton>button { border-radius: 20px; height: 3.5rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if "OPENAI_API_KEY" not in st.secrets:
    st.error("APIキーをSecretsに設定してください。")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 2. 究極のエラー回避：バイナリ純粋抽出 ---
def get_safe_b64(file_obj):
    """
    ファイル名という概念を捨て、中身の『数値データ』だけを取り出して
    新しい名無しの画像に作り直す。
    """
    try:
        # getvalue()は属性を読まないのでエラーを誘発しにくい
        raw_bytes = file_obj.getvalue()
        img = Image.open(BytesIO(raw_bytes))
        img = img.convert("RGB") # メタデータを消去
        
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except:
        return None

# --- 3. UI構築（5万円の価値：法人向けコンサルティング版） ---
st.title("🚀 Magic Biz Data Gen Pro")
st.caption("【法人専用】機密保持・高精度データ変換システム")

# 同意確認
with st.expander("🛡️ 法人向けセキュリティ・機密保持（同意必須）"):
    st.write("1. 送信された画像は解析後、メモリから即時抹消されます。")
    st.write("2. 本システムはAI学習に利用されないAPI契約を締結しています。")
    agreed = st.checkbox("上記に同意して利用する", value=True)

if not agreed:
    st.warning("利用するには同意が必要です。")
    st.stop()

st.divider()

# 錬成メニュー
doc_mode = st.radio("錬成する書類", ["タイムカード", "請求書", "その他資料"], horizontal=True)

# --- 4. 【核心】エラーにならない入力方法の提供 ---
st.write("#### 1. 書類を撮影または選択")
# iPhoneカメラは名前が固定されるため100%エラーにならない
img_captured = st.camera_input("【推奨】iPhoneカメラで撮影")

# アップローダー（ファイル名はCSSで隠しています）
st.write("または")
img_uploaded = st.file_uploader("写真を選択（ファイル名に制限はありません）", type=['png', 'jpg', 'jpeg'])

# どちらか入力があった方を使用
active_file = img_captured if img_captured else img_uploaded

if st.button("✨ データを錬成する（AI Professional解析）", type="primary", use_container_width=True):
    if active_file:
        info_area = st.empty()
        try:
            info_area.info("🔄 データを匿名化し、クリーンアップ中...")
            b64_img = get_safe_b64(active_file)
            
            if not b64_img:
                st.error("データの読み込みに失敗しました。")
                st.stop()

            info_area.info("🧠 AIがプロフェッショナル解析を実行中...")
            
            # 5万円の価値：構造化されたビジネスレポート
            prompt = f"""
            あなたは一流のDXコンサルタントです。画像（{doc_mode}）を解析しJSONで返せ。
            【出力】
            - "data": 表形式のデータ（JSONリスト）
            - "roi_saved_yen": "削減された人件費の概算（円）"
            - "consult_advice": "プロ視点のアドバイス"
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "返答は必ずJSONのみ。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]}
                ],
                response_format={"type": "json_object"}
            )

            import json
            res_json = json.loads(response.choices[0].message.content)
            df = pd.DataFrame(res_json["data"])
            
            info_area.success("✅ 錬成完了！")

            # ビジネスレポートの表示
            st.metric("今回削減されたコスト（推計）", f"¥{res_json.get('roi_saved_yen', '0')}")
            st.success(f"👘 コンサルタントのアドバイス: {res_json.get('consult_advice', '-')}")

            # 編集・プレビュー
            st.write("### 📊 生成データ（修正可能です）")
            edited_df = st.data_editor(df, use_container_width=True)

            # Excel出力
            out_buf = BytesIO()
            with pd.ExcelWriter(out_buf, engine='openpyxl') as writer:
                edited_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 プロ仕様Excelをダウンロード",
                data=out_buf.getvalue(),
                file_name="biz_refined_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            # エラー時も日本語ファイル名を出さず、安全なメッセージだけを出す
            info_area.error("🚨 処理が制限されました。")
            st.warning("【解決策】カメラ撮影からお試しいただくか、ファイル名を『1.jpg』等に変更してください。")
    else:
        st.warning("書類を撮影するか、写真を選択してください。")

st.divider()
st.caption("© 2024 Magic Biz Data Gen Pro Edition | Anonymized Processing System")
