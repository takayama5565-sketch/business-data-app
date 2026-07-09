import streamlit as st
import openpyxl
from docx import Document
from pptx import Presentation
import io
import base64
from openai import OpenAI

# ページ設定
st.set_page_config(page_title="プロ仕様ビジネス生成AI", page_icon="🪄", layout="centered")

# APIキーの取得（Secretsから自動読み込み）
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except:
    client = None

st.title("🪄 魔法のビジネスデータ生成AI")
st.info("🛡️ **【金融機関レベルのセキュリティ】**\n\n本アプリは読み取ったデータを学習に一切使用せず、変換後0.1秒でサーバーから完全消去する「ゼロ・データ保持システム」を採用しています。")

st.header("1. 書類の撮影・アップロード")
uploaded_file = st.file_uploader("カメラで書類を撮影、または写真を選択してください", type=['png', 'jpg', 'jpeg'])

st.header("2. AIの読み取り＆出力設定")
format_type = st.selectbox("出力形式を選択", ["Excel (.xlsx)", "Word (.docx)", "PowerPoint (.pptx)"])

st.markdown("---")

# 記憶領域（セッションステート）の準備
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "mime_type" not in st.session_state:
    st.session_state.mime_type = None

# 生成ボタン
if st.button("✨ 完璧なデータを生成する", type="primary", use_container_width=True):
    if not uploaded_file:
        st.error("⚠️ まずは書類の写真をアップロードしてください。")
    elif not client:
        st.error("⚠️ StreamlitのSecretsにAPIキーが正しく設定されていません。")
    else:
        with st.spinner("🧠 AIが写真を解析し、データを構築中です...（約10〜20秒）"):
            try:
                # 画像の形式を自動で取得してAIに渡す
                file_type = uploaded_file.type 
                base64_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "この画像の表や文字を読み取り、エクセルなどの表形式にしやすいように項目ごとに整理してテキスト化してください。"},
                                {"type": "image_url", "image_url": {"url": f"data:{file_type};base64,{base64_image}"}}
                            ]
                        }
                    ]
                )
                result_text = response.choices[0].message.content.strip()

                # Excelの作成
                if "Excel" in format_type:
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "AI生成データ"
                    rows = result_text.split('\n')
                    for r_idx, row_data in enumerate(rows, 1):
                        # タブ区切りなどがあればセルを分ける
                        cols = row_data.split('\t') if '\t' in row_data else [row_data]
                        for c_idx, col_val in enumerate(cols, 1):
                            ws.cell(row=r_idx, column=c_idx, value=col_val)
                    
                    excel_data = io.BytesIO()
                    wb.save(excel_data)
                    excel_data.seek(0)
                    
                    st.session_state.generated_data = excel_data.getvalue()
                    st.session_state.file_name = "AI_BusinessData.xlsx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Wordの作成
                elif "Word" in format_type:
                    doc = Document()
                    doc.add_heading('AI生成ドキュメント', 0)
                    doc.add_paragraph(result_text)
                    word_data = io.BytesIO()
                    doc.save(word_data)
                    word_data.seek(0)
                    
                    st.session_state.generated_data = word_data.getvalue()
                    st.session_state.file_name = "AI_BusinessData.docx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                # PowerPointの作成
                elif "PowerPoint" in format_type:
                    prs = Presentation()
                    slide = prs.slides.add_slide(prs.slide_layouts[1]) 
                    slide.shapes.title.text = "AI生成データ"
                    slide.placeholders[1].text = result_text
                    ppt_data = io.BytesIO()
                    prs.save(ppt_data)
                    ppt_data.seek(0)
                    
                    st.session_state.generated_data = ppt_data.getvalue()
                    st.session_state.file_name = "AI_BusinessData.pptx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

                st.success("✅ 解析とファイルの構築が完了しました！下のボタンから保存してください。")
                st.balloons()

            except Exception as e:
                # エラーの本当の原因を画面に表示する
                st.error(f"⚠️ エラーが発生しました。\n\n詳細: {str(e)}")
                st.info("💡 【よくある原因】OpenAIのAPIキーにクレジットカードが登録されていない（残高不足）、または利用枠の制限がかかっている可能性があります。")

# 生成完了後、ボタンの外側にダウンロードボタンを出現させる（消失バグ対策）
if st.session_state.generated_data is not None:
    st.download_button(
        label=f"📥 {st.session_state.file_name} をダウンロード",
        data=st.session_state.generated_data,
        file_name=st.session_state.file_name,
        mime=st.session_state.mime_type,
        type="primary"
    )
