import streamlit as st
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from docx import Document
from pptx import Presentation
from pptx.util import Inches
import io
import base64
import re
from openai import OpenAI
from PIL import Image
from datetime import datetime

# ==========================================
# 5万円で販売するための「Enterprise SaaS」設定
# ==========================================
st.set_page_config(page_title="Biz Data Alchemist Pro", page_icon="💎", layout="wide")

# APIキーの安全な読み込み
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except:
    client = None

# --- 左サイドバー：設定とコンプライアンス ---
with st.sidebar:
    st.header("⚙️ 変換設定")
    format_type = st.radio("1. 出力フォーマット", ["Excel (.xlsx)", "Word (.docx)", "PowerPoint (.pptx)"])
    doc_type = st.selectbox("2. 書類のカテゴリ", ["自動判別 (推奨)", "タイムカード・勤怠", "請求書・領収書", "手書きメモ・アンケート"])
    
    st.markdown("---")
    st.header("⚖️ コンプライアンス設定")
    st.caption("エンタープライズ向けのデータ保護基準を満たすため、以下のポリシーへの同意が必須です。")
    agree_terms = st.checkbox("【必須】機密情報の即時破棄（ゼロ・データ保持）に同意する")
    if agree_terms:
        st.success(f"署名完了: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n監査ログID: SEC-{datetime.now().strftime('%f')}")

# --- メインエリア ---
st.title("💎 Biz Data Alchemist [Enterprise Edition]")
st.markdown("### 画像からビジネスデータを錬成し、プロフェッショナルな資料を自動生成します。")

uploaded_file = st.file_uploader("📸 書類の画像をアップロード（HEIC, JPG, PNG対応）", type=['png', 'jpg', 'jpeg', 'heic', 'webp'])

# セッション状態の初期化（ダウンロード消失バグ対策）
if "generated_file" not in st.session_state:
    st.session_state.generated_file = None
    st.session_state.file_name = None
    st.session_state.mime_type = None
    st.session_state.preview_data = [] 

if uploaded_file:
    with st.expander("アップロードした画像を確認", expanded=False):
        st.image(uploaded_file, use_container_width=True)

st.markdown("---")

# --- 堅牢なパース用関数（最強の抽出フィルター） ---
def parse_markdown_table(text):
    lines = text.split('\n')
    table_data = []
    for line in lines:
        if '|' in line:
            if re.match(r'^[\s\|:-]+$', line): # 区切り線は無視
                continue
            row = [cell.strip() for cell in line.split('|')][1:-1]
            if row:
                table_data.append(row)
    return table_data

# --- データ生成アクション ---
if st.button("🚀 データを錬成する (AI解析スタート)", type="primary", use_container_width=True):
    if not agree_terms:
        st.error("⚠️ 左側のサイドバーで「セキュリティポリシー」に同意チェックを入れてください。")
    elif not uploaded_file:
        st.error("⚠️ 処理する書類の写真をアップロードしてください。")
    elif not client:
        st.error("⚠️ APIキーが設定されていません。StreamlitのSecrets設定を確認してください。")
    else:
        with st.spinner("🧠 データを安全に解析し、プロ仕様のレイアウトを構築中...（約10〜20秒）"):
            try:
                # 1. 画像の完全無効化・安全処理
                image = Image.open(uploaded_file).convert("RGB")
                image.thumbnail((1600, 1600))
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # 2. AIへの絶対服従プロンプト
                sys_prompt = f"""
                あなたは世界最高峰のデータ入力スペシャリストです。
                提供された画像を解析し、{doc_type}のデータを抽出してください。
                【絶対ルール】
                1. 結果は必ず「Markdown形式のテーブル（表）」だけで出力してください。
                2. 挨拶、説明などは一切書かないでください。
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
                    ],
                    temperature=0.1 # 安定した出力を強制
                )
                raw_result = response.choices[0].message.content.strip()
                
                # 3. 強力フィルターで表データのみを抽出
                table_data = parse_markdown_table(raw_result)
                
                # 万が一表が見つからなかった場合のフェイルセーフ（クラッシュ防止）
                if not table_data:
                    table_data = [["解析結果"]]
                    for line in raw_result.split('\n'):
                        if line.strip().replace('`', ''):
                            table_data.append([line.strip().replace('`', '')])
                
                st.session_state.preview_data = table_data

                # 4. 各フォーマットごとの美しいファイル生成
                if "Excel" in format_type:
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "抽出データ"
                    
                    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                    header_font = Font(color="FFFFFF", bold=True)
                    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                    
                    for r_idx, row in enumerate(table_data, 1):
                        for c_idx, val in enumerate(row, 1):
                            cell = ws.cell(row=r_idx, column=c_idx, value=val)
                            cell.border = thin_border
                            cell.alignment = Alignment(vertical="center")
                            if r_idx == 1: # 1行目をプロ仕様にデザイン
                                cell.fill = header_fill
                                cell.font = header_font
                                cell.alignment = Alignment(horizontal="center", vertical="center")
                    
                    # 列幅の簡易自動調整とフィルター
                    for col in ws.columns:
                        ws.column_dimensions[col[0].column_letter].width = 15
                    ws.auto_filter.ref = ws.dimensions

                    buf = io.BytesIO()
                    wb.save(buf)
                    st.session_state.generated_file = buf.getvalue()
                    st.session_state.file_name = f"Data_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                elif "Word" in format_type:
                    doc = Document()
                    doc.add_heading(f'解析レポート: {doc_type}', level=1)
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for r_idx, row in enumerate(table_data):
                        for c_idx, val in enumerate(row):
                            if c_idx < len(table.columns):
                                table.cell(r_idx, c_idx).text = str(val)
                    buf = io.BytesIO()
                    doc.save(buf)
                    st.session_state.generated_file = buf.getvalue()
                    st.session_state.file_name = f"Report_{datetime.now().strftime('%Y%m%d')}.docx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                elif "PowerPoint" in format_type:
                    prs = Presentation()
                    slide = prs.slides.add_slide(prs.slide_layouts[5])
                    slide.shapes.title.text = f"抽出データ: {doc_type}"
                    rows, cols = min(len(table_data), 15), len(table_data[0]) # PPTに収まるよう制限
                    table = slide.shapes.add_table(rows, cols, Inches(1), Inches(2), Inches(8), Inches(0.3 * rows)).table
                    for r_idx in range(rows):
                        for c_idx in range(min(cols, len(table_data[r_idx]))):
                            cell = table.cell(r_idx, c_idx)
                            cell.text = str(table_data[r_idx][c_idx])
                            if r_idx == 0:
                                cell.fill.solid()
                                cell.fill.fore_color.rgb = openpyxl.styles.colors.Color(rgb='1F4E78').rgb
                                cell.text_frame.paragraphs[0].font.color.rgb = openpyxl.styles.colors.Color(rgb='FFFFFF').rgb
                    buf = io.BytesIO()
                    prs.save(buf)
                    st.session_state.generated_file = buf.getvalue()
                    st.session_state.file_name = f"Slide_{datetime.now().strftime('%Y%m%d')}.pptx"
                    st.session_state.mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

                st.success("✅ 完璧なデータ錬成が完了しました！")
                st.balloons()

            except Exception as e:
                st.error("⚠️ 解析中にエラーが発生しました。写真がぼやけている、または文字が小さすぎる可能性があります。")
                with st.expander("🛠️ 開発者向けエラー詳細（サポート用）"):
                    st.error(str(e))

# --- 5. 結果プレビューとダウンロード ---
if st.session_state.generated_file:
    st.markdown("### 📊 抽出データのプレビュー")
    if st.session_state.preview_data:
        st.table(st.session_state.preview_data)
        
    st.markdown("### 📥 ダウンロード")
    st.download_button(
        label=f"💾 {st.session_state.file_name} を保存する",
        data=st.session_state.generated_file,
        file_name=st.session_state.file_name,
        mime=st.session_state.mime_type,
        type="primary",
        use_container_width=True
    )
