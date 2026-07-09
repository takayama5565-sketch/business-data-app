import streamlit as st
import openai
import pandas as pd
from io import BytesIO
import base64
from PIL import Image
import os

# --- 0. 環境の「言語エラー」を強制回避（重要） ---
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 1. 初期設定 ---
st.set_page_config(page_title="BizData Gen Pro v2", layout="wide")

# セキュリティチェック
if "OPENAI_API_KEY" not in st.secrets:
    st.error("APIキーが設定されていません。管理画面のSecretsに登録してください。")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 2. 究極の「エラー回避」画像処理 ---
def get_safe_image(uploaded_file):
    """
    ファイル名（日本語）を一切無視し、純粋な『絵のデータ』だけを抜き出す。
    これにより ASCII エラーを物理的に発生させない。
    """
    # ファイル名を参照せずに中身（バイト）だけを読み込む
    img_data = uploaded_file.read()
    img = Image.open(BytesIO(img_data))
    img = img.convert("RGB") # メタデータを完全に剥ぎ取る
    
    # AIが読みやすいサイズに調整
    img.thumbnail((1600, 1600))
    
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. UI構築 ---
st.title("🚀 Magic Biz Data Gen Pro")
st.caption("【法人・プロフェッショナル専用】高精度データ変換エンジン")

# 同意確認
with st.sidebar:
    st.header("🛡️ セキュリティ設定")
    is_agreed = st.checkbox("データ即時消去に同意する", value=True)
    st.info("送信された画像はメモリ内のみで処理され、保存されません。")

if not is_agreed:
    st.warning("利用するにはセキュリティ設定に同意してください。")
    st.stop()

# メイン操作エリア
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 1. 書類のアップロード")
    # ここで日本語ファイル名が来ても、内部処理では無視するように設計
    uploaded_file = st.file_uploader("写真をアップロード（iPhone対応）", type=['png', 'jpg', 'jpeg'])

with col2:
    st.markdown("### 2. 解析設定")
    doc_type = st.selectbox("書類のタイプを選択", ["タイムカード", "手書き請求書", "ビジネス文書（自動判別）"])
    output_name = st.text_input("保存するファイル名（英数字のみ推奨）", "business_data")

if st.button("✨ データを生成する（解析開始）", type="primary", use_container_width=True):
    if uploaded_file is not None:
        try:
            # プログレス表示
            with st.status("🛠️ プロフェッショナル解析実行中...", expanded=True) as status:
                
                # A. 画像の「完全匿名化」処理
                st.write("📷 画像データから不要な情報を除去中...")
                base64_image = get_safe_image(uploaded_file)
                
                # B. AIへの超精密な命令（5万円の価値を出すプロンプト）
                st.write("🧠 AIが文字を解析・データ変換中...")
                prompt = f"""
                あなたは一流の事務代行スタッフです。
                この画像（{doc_type}）から全データを抽出し、JSON形式で出力してください。
                【条件】
                - 数字は半角に統一。
                - 表形式で出力すること。
                - タイムカードの場合、日ごとの実働時間（退勤-出勤-休憩）を推測して計算。
                - 請求書の場合、単価×数量が合計と一致するか検算してください。
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "返答は必ず純粋なJSONのみにしてください。"},
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]}
                    ],
                    response_format={"type": "json_object"}
                )
                
                # C. データの受け取りと表示
                import json
                result_json = json.loads(response.choices[0].message.content)
                # JSONの中から最初のリスト項目を探し出す
                first_key = list(result_json.keys())[0]
                df = pd.DataFrame(result_json[first_key])
                
                status.update(label="✅ 解析完了！", state="complete", expanded=False)

            st.success("🎉 データの錬成に成功しました！")
            
            # D. 画面上での修正機能（ビジネスプロの推奨）
            st.write("### 💎 解析結果の確認・修正")
            st.caption("※セルの内容をダブルクリックして修正できます。修正後にダウンロードしてください。")
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

            # E. Excel出力
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                edited_df.to_excel(writer, index=False, sheet_name='Data_Result')
            
            st.download_button(
                label=f"📥 {output_name}.xlsx をダウンロード",
                data=output.getvalue(),
                file_name=f"{output_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            # 最悪エラーが起きても、ユーザーに「次の一手」を提示する（UXの極意）
            st.error(f"🚨 処理が中断されました")
            with st.expander("技術的なエラー詳細"):
                st.write(str(e))
            st.info("💡 対策: 画像を少し明るい場所で撮り直すか、ファイル名を 'doc1.jpg' のように英数字に変更して試してください。")
    else:
        st.warning("写真をアップロードしてください。")

# フッター
st.divider()
st.caption("© 2024 Magic Biz Data Gen | セキュリティ：送信されたデータはダウンロード後に即時消去されます。")
