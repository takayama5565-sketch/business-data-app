import streamlit as st
import openpyxl
from docx import Document
from pptx import Presentation
import io
import base64
from openai import OpenAI
from PIL import Image

# --- 1. ページ設定とセキュリティ ---
st.set_page_config(page_title="Magic Biz Data Pro", page_icon="🪄", layout="wide")

try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except:
    client = None

# --- 2. 左側：プロ仕様サイドバー設定 ---
with st.sidebar:
    st.title("⚙️ 出力・セキュリティ設定")
    format_type = st.selectbox("1. 出力ファイル形式", ["Excel (.xlsx)", "Word (.docx)", "PowerPoint (.pptx)"])
    doc_type = st.selectbox("2. 書類の種類", ["自動判別", "タイムカード", "請求書・見積書", "手書き表・アンケート"])
    
    st.markdown("---")
    st.caption("🛡️ 法人向けセキュリティ")
    agree_terms = st.checkbox("【必須】利用規約およびデータ即時破棄に同意する")

# --- 3. 中央：メイン操作画面 ---
st.title("🪄 魔法のビジネスデータ生成AI [Pro版]")
st.markdown("どんなファイル名の写真でも、AIが安全に高精度なビジネスデータに変換します。")

uploaded_file = st.file_uploader("📸 ここに書類の写真をドロップ、またはカメラで撮影", type=['png', 'jpg', 'jpeg', 'heic', 'webp'])

# ダウンロード用データの記憶領域
if "generated_file" not in st.session_state:
    st.session_state.generated_file = None
    st.session_state.file_name = None
    st.session_state.mime_type = None

# プレビュー表示
if uploaded_file:
    st.image(uploaded_file, caption="アップロードされた画像", use_container_width=True)

# --- 4. 生成処理（最強の安全エンジン） ---
if st.button("✨ 完璧なデータを生成する", type="primary", use_container_width=True):
    if not agree_terms:
        st.error("⚠️ エラー：左側の「利用規約およびデータ即時破棄に同意する」にチェックを入れてください。")
    elif not uploaded_file:
        st.error("⚠️ エラー：処理する写真をアップロードしてください。")
    elif not client:
        st.error("⚠️ エラー：システム管理者にお問い合わせください。（APIキー未設定）")
    else:
        with st.spinner("🧠 独自の画像最適化フィルターを通し、AI解析を実行中...（約10〜20秒）"):
            try:
                # 【重要】どんなファイル名でも無効化し、安全な画像データに変換する処理
                image = Image.open(uploaded_file)
                image = image.convert("RGB") # 特殊形式の無効化
                image.thumbnail((1600, 1600)) # 巨大画像を軽量化
                
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                sys_prompt = f"あなたはプロのデータアナリストです。提供された画像を解析し、{doc_type}として最適な形でテキストを抽出してください。無駄な挨拶は省き、データのみを綺麗な表形式（カンマまたはタブ区切り）で出力してください。"
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]}
                    ]
                )
                ai_result = response.choices[0].message.content.strip()

                if "Excel" in format_type:
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "AI生成データ"
                    
                    for r_idx, row_data in enumerate(ai_result.split('\n'), 1):
                        cols = row_data.split(',') if ',' in row_data else row_data.split('\t') if '\t' in row_data else [row_data]
                        for c_idx, col_val in enumerate(cols, 1):
                            ws.cell(row=r_idx, column=c_idx, value=col_val.strip())
                            
                    buf = io.BytesIO()
                    wb.save(buf)
                    st.session_state.generated_file = buf.getvalue()
                    st.session_state.file_name = "Pro_BusinessData.xlsx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                elif "Word" in format_type:
                    doc = Document()
                    doc.add_heading(f'AI生成ドキュメント ({doc_type})', level=1)
                    doc.add_paragraph(ai_result)
                    buf = io.BytesIO()
                    doc.save(buf)
                    st.session_state.generated_file = buf.getvalue()
                    st.session_state.file_name = "Pro_BusinessData.docx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                elif "PowerPoint" in format_type:
                    prs = Presentation()
                    slide = prs.slides.add_slide(prs.slide_layouts[1])
                    slide.shapes.title.text = f"AI生成データ ({doc_type})"
                    slide.placeholders[1].text = ai_result
                    buf = io.BytesIO()
                    prs.save(buf)
                    st.session_state.generated_file = buf.getvalue()
                    st.session_state.file_name = "Pro_BusinessData.pptx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

                st.success("✅ データの錬成に成功しました！以下のボタンからダウンロードしてください。")
                st.balloons()

            except Exception as e:
                st.error("⚠️ 処理中にエラーが発生しました。")
                st.info(f"開発者用詳細: {str(e)}")

# --- 5. ダウンロードボタンの表示 ---
if st.session_state.generated_file:
    st.markdown("### 📥 ダウンロード準備完了")
    st.download_button(
        label=f"💾 {st.session_state.file_name} を保存する",
        data=st.session_state.generated_file,
        file_name=st.session_state.file_name,
        mime=st.session_state.mime_type,
        type="primary"
    )
