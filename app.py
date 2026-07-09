import streamlit as st
import openpyxl
from docx import Document
from pptx import Presentation
import io
import base64
from openai import OpenAI

# StreamlitのSecretsからAPIキーを取得
api_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

st.set_page_config(page_title="Magic Biz Data Gen", page_icon="🪄", layout="centered")
st.title("🪄 魔法のビジネスデータ生成AI [Pro]")

# 1. 撮影・アップロード
uploaded_file = st.file_uploader("書類の写真をアップロードしてください", type=['png', 'jpg', 'jpeg'])

# 2. 設定
col1, col2 = st.columns(2)
with col1: format_type = st.selectbox("出力形式", ["Excel (.xlsx)", "Word (.docx)", "PowerPoint (.pptx)"])
with col2: doc_type = st.selectbox("書類タイプ", ["タイムカード", "請求書", "その他"])

# 3. 処理開始
if st.button("✨ データを生成する", type="primary"):
    if not uploaded_file or not client:
        st.error("⚠️ 写真をアップロードするか、APIキーを確認してください。")
    else:
        with st.spinner("🧠 解析中...しばらくお待ちください"):
            try:
                base64_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
                
                # AIへの指示（プロンプト）
                prompt = f"あなたはプロの事務職です。この{doc_type}の画像を読み取り、項目と値を整理して、ExcelやWordで編集しやすいきれいな表形式のテキストデータのみを抽出してください。"
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}]
                )
                result_text = response.choices[0].message.content
                
                # 記憶領域に保存（セッションステート）
                st.session_state.data = result_text
                st.session_state.format = format_type
                st.success("✅ データ化完了！")
                
            except Exception as e:
                st.error(f"⚠️ 解析エラー: {str(e)}")

# 4. ダウンロードボタン（消失バグ対策：ボタンを独立させる）
if "data" in st.session_state:
    if "Excel" in st.session_state.format:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["内容"])
        ws.append([st.session_state.data])
        buf = io.BytesIO()
        wb.save(buf)
        st.download_button("📥 Excelダウンロード", buf.getvalue(), "BusinessData.xlsx")
    elif "Word" in st.session_state.format:
        doc = Document()
        doc.add_paragraph(st.session_state.data)
        buf = io.BytesIO()
        doc.save(buf)
        st.download_button("📥 Wordダウンロード", buf.getvalue(), "BusinessData.docx")
    elif "PowerPoint" in st.session_state.format:
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = "解析結果"
        slide.placeholders[1].text = st.session_state.data
        buf = io.BytesIO()
        prs.save(buf)
        st.download_button("📥 PPTダウンロード", buf.getvalue(), "BusinessData.pptx")

# フッター（法的信頼性のアピール）
st.markdown("---")
st.caption("© 2026 Magic Biz Data Gen | [利用規約] | [プライバシーポリシー]")
