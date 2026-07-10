import os
import sys
import locale

# --- 0. システム環境のUTF-8化（日本語エラーを物理的に遮断） ---
try:
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
except:
    pass
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
import google.generativeai as genai
import pandas as pd
from io import BytesIO
from PIL import Image
import json

# --- 1. HEIC形式（iPhone独自形式）のデコーダーを登録 ---
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# --- 2. アプリ初期設定 ---
st.set_page_config(page_title="BizAlchemy Free Demo", layout="wide")

# CSSでファイル名表示部を保護（表示によるエンコードエラーを回避）
st.markdown("""
    <style>
    [data-testid="stFileUploaderFileName"] { display: none; }
    .stApp { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# SecretsからGemini APIキーを取得（無料枠用）
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini APIキーをSecretsに設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. 匿名画像データ生成エンジン ---
def get_safe_pil_image(uploaded_file):
    """
    ファイル名などの属性を完全遮断し、
    HEIC等の画像も自動でRGB互換に変換して純粋なPIL画像としてメモリに展開する。
    """
    try:
        raw_bytes = uploaded_file.getvalue()
        img = Image.open(BytesIO(raw_bytes))
        img = img.convert("RGB") # メタデータを消去
        img.thumbnail((1200, 1200)) # AI処理に適したサイズに調整
        return img
    except Exception:
        return None

# --- 4. 各種フォーマット出力エンジン ---
def generate_multiformat(df, advice, format_type):
    output = BytesIO()
    
    if format_type == "Excel (.xlsx)":
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"

    elif format_type == "Word (.docx)":
        from docx import Document
        doc = Document()
        doc.add_heading('AI Business Analysis Report', 0)
        doc.add_heading('1. 抽出データ', level=1)
        table = doc.add_table(rows=1, cols=len(df.columns))
        for i, col in enumerate(df.columns): table.rows[0].cells[i].text = str(col)
        for _, row in df.iterrows():
            row_cells = table.add_row().cells
            for i, val in enumerate(row): row_cells[i].text = str(val)
        doc.add_heading('2. 経営アドバイス', level=1)
        doc.add_paragraph(advice)
        doc.save(output)
        return output.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"

    elif format_type == "PowerPoint (.pptx)":
        from pptx import Presentation
        prs = Presentation()
        slide1 = prs.slides.add_slide(prs.slide_layouts[0])
        slide1.shapes.title.text = "AI分析結果"
        slide1.placeholders[1].text = "ビジネスデータ錬成エンジン Free v8"
        slide2 = prs.slides.add_slide(prs.slide_layouts[1])
        slide2.shapes.title.text = "経営インサイト"
        slide2.placeholders[1].text = advice
        prs.save(output)
        return output.getvalue(), "application/vnd.openxmlformats-officedocument.presentationml.presentation", "pptx"

# --- 5. メインUI ---
st.title("🚀 Magic Biz Data Gen - Free Demo")
st.write("### ～ 完全無料で動く、AIビジネスデータ錬成エンジンの実証デモ ～")

# 弁護士視点：無料枠特有のデータ取扱い同意フロー
with st.expander("🛡️ デモ版の機密保持とセキュリティについて（お読みください）"):
    st.warning("【ご注意】本デモ版はGoogleの無料APIを利用しているため、送信された画像がAIモデルの向上に一時利用される可能性があります。個人情報や極秘データはマスクするか、テスト用画像をご利用ください。")
    st.info("💡 法人向けの『本番（有料）ライセンス』では、データは暗号化され、学習に一切流用されずに1秒以内に消去される専用API（OpenAI等）に切り替わります。")
    is_agreed = st.checkbox("上記に同意してデモを開始する", value=True)

if is_agreed:
    # 設定セクション
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        doc_type = st.selectbox("📝 書類の種類", ["タイムカード（勤怠計算）", "手書き請求書", "その他ビジネス文書"])
    with col_u2:
        out_format = st.radio("📁 出力ファイル形式", ["Excel (.xlsx)", "Word (.docx)", "PowerPoint (.pptx)"], horizontal=True)

    # アップローダー
    uploaded_file = st.file_uploader("書類をアップロード（日本語名・iPhoneのHEIC形式に対応済み）", type=['png', 'jpg', 'jpeg', 'heic', 'HEIC'])

    if st.button("✨ データを錬成する", type="primary", use_container_width=True):
        if uploaded_file:
            msg = st.empty()
            try:
                msg.info("📷 画像データを最適化中（ファイル名を安全に除去）...")
                img_obj = get_safe_pil_image(uploaded_file)
                
                if not img_obj:
                    st.error("🚨 画像の読み込みに失敗しました。ファイルが破損していないか確認してください。")
                    st.stop()

                msg.info("🧠 Gemini AI（無料枠）がデータを解析中...")
                
                # Gemini用モデル（1.5 Flash）を構築し、JSONで出力を強制します
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    generation_config={"response_mime_type": "application/json"}
                )

                prompt = f"""
                あなたは優秀なDXコンサルタントです。この画像（{doc_type}）から全データを抽出してください。
                【出力形式】
                必ず以下のキーを持つJSON形式で出力してください：
                {{
                  "data": [{{"項目名": "値"}}],
                  "cost_saved": 想定削減時間（分、数値のみ）,
                  "advice": "経営改善アドバイス一言"
                }}
                """

                # PILのイメージオブジェクトとプロンプトを直接Geminiに送信（ファイル名を介さないためエラーが起きません）
                response = model.generate_content([prompt, img_obj])
                
                # 結果をパース
                result = json.loads(response.text)
                df = pd.DataFrame(result["data"])
                advice = result.get("advice", "解析完了しました。")
                saved_time = result.get("cost_saved", 20)

                msg.success(f"✅ 錬成完了！約{saved_time}分の事務作業を削減しました（想定 ¥{saved_time * 50}円相当の価値）。")

                # プレビュー表示
                st.write("### 💎 錬成結果プレビュー")
                edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
                st.info(f"💡 AIコンサルのアドバイス: {advice}")

                # ファイル生成とダウンロード
                file_data, mime, ext = generate_multiformat(edited_df, advice, out_format)

                st.download_button(
                    label=f"📥 {out_format} をダウンロードする",
                    data=file_data,
                    file_name=f"biz_refined_demo.{ext}",
                    mime=mime,
                    use_container_width=True
                )

            except Exception as e:
                msg.error("🚨 解析中に問題が発生しました。")
                st.warning("Gemini APIの1分あたりのアクセス制限を超えた可能性があります。少し待ってから再度お試しください。")
                print(f"Error detail: {str(e)}")
        else:
            st.warning("ファイルをアップロードしてください。")
else:
    st.info("同意にチェックを入れるとデモが開始できます。")

st.divider()
st.caption("© 2024 Magic Biz Data Gen Pro | Google Gemini Free API Module Built")
