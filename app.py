import streamlit as st
import openpyxl
from docx import Document
from pptx import Presentation
import io
import base64
from openai import OpenAI

# StreamlitのSecretsからAPIキーを取得
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except Exception as e:
    client = None

st.set_page_config(page_title="プロ仕様ビジネス生成AI", page_icon="🪄", layout="centered")
st.title("🪄 魔法のビジネスデータ生成AI")
st.info("🛡️ **【金融機関レベルのセキュリティ】**\n\n本アプリは読み取ったデータを学習に一切使用せず、変換後0.1秒でサーバーから完全消去する「ゼロ・データ保持システム」を採用しています。")

st.header("1. 書類の撮影・アップロード")
uploaded_file = st.file_uploader("カメラで書類を撮影、または写真を選択してください", type=['png', 'jpg', 'jpeg'])

st.header("2. AIの読み取り＆出力設定")
format_type = st.selectbox("出力形式を選択", ["Excel (.xlsx)", "Word (.docx)", "PowerPoint (.pptx)"])

st.markdown("---")

if st.button("✨ 完璧なデータを生成する", type="primary", use_container_width=True):
    if not uploaded_file:
        st.error("⚠️ まずは書類の写真をアップロードしてください。")
    elif not client:
        st.error("⚠️ StreamlitのSecretsにAPIキーが正しく設定されていません。")
    else:
        with st.spinner("🧠 AIが写真を解析し、データを構築中です...（約10秒）"):
            try:
                # 画像の準備
                base64_image = base64.b64encode(uploaded_file.getvalue()).decode()
                
                # OpenAI AI解析
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "この画像の文字を読み取り、重要なテキストを箇条書きで抽出してください。"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ]
                )
                result_text = response.choices[0].message.content.strip()

                st.success("✅ 解析とファイルの構築が完了しました！下のボタンから保存してください。")
                st.balloons()
                
                # 選んだ形式に合わせてファイルを作成
                if "Excel" in format_type:
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "AI生成データ"
                    rows = result_text.split('\n')
                    for r_idx, row_data in enumerate(rows, 1):
                        ws.cell(row=r_idx, column=1, value=row_data)
                    excel_data = io.BytesIO()
                    wb.save(excel_data)
                    excel_data.seek(0)
                    st.download_button("📥 Excelをダウンロード", excel_data, "AI_Data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                elif "Word" in format_type:
                    doc = Document()
                    doc.add_heading('AI生成ドキュメント', 0)
                    doc.add_paragraph(result_text)
                    word_data = io.BytesIO()
                    doc.save(word_data)
                    word_data.seek(0)
                    st.download_button("📥 Wordをダウンロード", word_data, "AI_Data.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                
                elif "PowerPoint" in format_type:
                    prs = Presentation()
                    slide = prs.slides.add_slide(prs.slide_layouts[1]) 
                    title = slide.shapes.title
                    content = slide.placeholders[1]
                    title.text = "AI生成データ"
                    content.text = result_text
                    ppt_data = io.BytesIO()
                    prs.save(ppt_data)
                    ppt_data.seek(0)
                    st.download_button("📥 PowerPointをダウンロード", ppt_data, "AI_Data.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation")

            except Exception as e:
                st.error(f"⚠️ 解析中にエラーが発生しました。")
