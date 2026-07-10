import streamlit as st
import openpyxl
from docx import Document
from pptx import Presentation
import io
import base64
from openai import OpenAI

# --- 1. ページ全体の初期設定（プロ仕様の広いレイアウト） ---
st.set_page_config(page_title="Magic Biz Data Pro", page_icon="🪄", layout="wide")

# APIキーの安全な読み込み
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except:
    client = None

# --- 2. サイドバー（左側の設定パネル） ---
with st.sidebar:
    st.title("⚙️ 出力設定")
    format_type = st.selectbox("1. 出力ファイル形式", ["Excel (.xlsx)", "Word (.docx)", "PowerPoint (.pptx)"])
    doc_type = st.selectbox("2. 書類の種類", ["自動判別", "タイムカード", "請求書・見積書", "アンケート・手書き表"])
    
    st.markdown("---")
    st.caption("🛡️ セキュリティ設定")
    # 法的防衛のための同意チェックボックス（5万円の価値）
    agree_terms = st.checkbox("利用規約およびデータ即時破棄（ゼロ・データ保持）に同意する")

# --- 3. メイン画面（右側の操作パネル） ---
st.title("🪄 魔法のビジネスデータ生成AI [Pro版]")
st.info("左側のサイドバーで出力形式を設定し、書類の写真をアップロードしてください。")

uploaded_file = st.file_uploader("📸 ここに書類の写真をドロップ、またはカメラで撮影", type=['png', 'jpg', 'jpeg', 'heic'])

# 記憶領域の初期化
if "generated_file" not in st.session_state:
    st.session_state.generated_file = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "mime_type" not in st.session_state:
    st.session_state.mime_type = None

# --- 4. データ生成アクション ---
if st.button("✨ 完璧なデータを生成する", type="primary", use_container_width=True):
    # エラーチェック（法的同意、ファイル有無、API）
    if not agree_terms:
        st.error("⚠️ エラー：左側の「利用規約およびデータ即時破棄に同意する」にチェックを入れてください。")
    elif not uploaded_file:
        st.error("⚠️ エラー：処理する写真をアップロードしてください。")
    elif not client:
        st.error("⚠️ エラー：システム管理者にお問い合わせください。（APIキー未設定）")
    else:
        with st.spinner("🧠 高度なAI解析を実行中...（約10〜20秒かかります）"):
            try:
                # 【重要修正】ファイル名を完全に無視し、純粋な画像データ（バイナリ）として強制処理
                image_bytes = uploaded_file.getvalue()
                base64_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # プロ仕様のAIへの命令
                sys_prompt = f"あなたはプロのデータ入力スペシャリストです。提供された画像を解析し、{doc_type}として最適な形でテキストを抽出してください。無駄な挨拶は省き、データのみを綺麗な表形式（または箇条書き）で出力してください。"
                
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

                # --- 形式ごとのファイル作成処理 ---
                if "Excel" in format_type:
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "AI生成データ"
                    
                    # データをエクセルのセルに分割して入れる
                    for r_idx, row_data in enumerate(ai_result.split('\n'), 1):
                        cols = row_data.split(',') if ',' in row_data else row_data.split(' ')
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
                st.error("⚠️ AIの解析中に予期せぬエラーが発生しました。")
                st.info(f"開発者用エラーコード: {str(e)}")

# --- 5. ダウンロードボタン（生成後に表示） ---
if st.session_state.generated_file:
    st.markdown("### 📥 ダウンロード準備完了")
    st.download_button(
        label=f"💾 {st.session_state.file_name} を保存する",
        data=st.session_state.generated_file,
        file_name=st.session_state.file_name,
        mime=st.session_state.mime_type,
        type="primary"
    )
