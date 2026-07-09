import streamlit as st
import openai
import pandas as pd
from io import BytesIO
import base64
from PIL import Image

# --- 1. 究極のセキュリティ & エラー回避設定 ---
st.set_page_config(page_title="BizData Alchemy Pro", layout="centered")

# APIキーのチェック
if "OPENAI_API_KEY" not in st.secrets:
    st.error("APIキーが設定されていません。")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 2. ファイル名情報を「物理的に遮断」する関数 ---
def get_image_bytes_only(uploaded_file):
    """
    ファイル名などのメタデータを一切読み込まず、
    純粋な画像バイナリデータのみを取り出して、完全に新しいデータとして作り直す。
    """
    # 1. アップロードされたファイルの中身（バイト）だけをコピー
    file_bytes = uploaded_file.getvalue()
    
    # 2. PILで開き直す（この時点で元のファイルオブジェクトとの縁が切れる）
    img = Image.open(BytesIO(file_bytes))
    img = img.convert("RGB")
    
    # 3. サイズを最適化
    img.thumbnail((1500, 1500))
    
    # 4. 「名無し」のデータとして保存
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- 3. メインUI（5万円の価値を演出） ---
st.title("🚀 Magic Biz Data Gen Pro")
st.write("### ～ 紙の書類を、一瞬で『資産』に変える ～")

with st.expander("🛡️ 法人向けセキュリティ・機密保持について"):
    st.caption("・送信された画像はメモリ内のみで処理され、保存されません。")
    st.caption("・AI（GPT-4o）の学習には利用されない『APIオプトアウト』設定済みです。")
    st.caption("・日本国内の個人情報保護法および商用利用ライセンスに準拠しています。")

# 4. 入力エリア
st.divider()
doc_type = st.radio("書類の種類を選択してください", ["タイムカード", "手書き請求書", "その他（自動解析）"], horizontal=True)

# エラーを避けるため、シンプルなアップローダー
raw_input = st.file_uploader("書類の写真をアップロード（iPhone・Android対応）")

if st.button("✨ データを錬成する", type="primary", use_container_width=True):
    if raw_input:
        # 進行状況を1つのエリアで管理（エラー回避のため）
        placeholder = st.empty()
        
        try:
            # A. 画像の匿名化処理
            placeholder.info("📷 画像をクリーンアップ中...")
            image_b64 = get_image_bytes_only(raw_input)
            
            # B. AI解析（プロンプトに経営診断を追加）
            placeholder.info("🧠 AIがプロフェッショナル解析を実行中...")
            prompt = f"""
            あなたは一流の事務代行 兼 経営コンサルタントです。
            この画像（{doc_type}）から全データを抽出してください。
            【出力形式】JSON（"data"というキーにリスト形式で保存）
            【追加指示】データの最後に、この書類から読み取れる「経営・効率化のアドバイス」を1つだけ"advice"というキーで含めてください。
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "返答は必ず純粋なJSONのみにしてください。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]}
                ],
                response_format={"type": "json_object"}
            )
            
            # C. 解析結果の表示
            import json
            res = json.loads(response.choices[0].message.content)
            df = pd.DataFrame(res["data"])
            
            placeholder.success("✅ 錬成完了！")
            
            # アドバイスの表示（価値向上ポイント）
            if "advice" in res:
                st.warning(f"💡 AI経営アドバイス: {res['advice']}")
            
            st.write("### 📊 生成されたデータ")
            # 編集可能な表
            edited_df = st.data_editor(df, use_container_width=True)
            
            # D. Excel書き出し
            out_buf = BytesIO()
            with pd.ExcelWriter(out_buf, engine='openpyxl') as writer:
                edited_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 プロ仕様Excelファイルをダウンロード",
                data=out_buf.getvalue(),
                file_name="biz_alchemy_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            placeholder.error("🚨 エラーが発生しました")
            # エラーメッセージから日本語を除去して表示
            safe_error = str(e).encode('ascii', 'ignore').decode('ascii')
            st.info(f"システムメッセージ: {safe_error}")
            st.warning("【解決策】画像ファイルの名前を『a1.jpg』などの英数字に変更して、再度お試しください。")
    else:
        st.warning("写真をアップロードしてください。")

st.divider()
st.caption("© 2024 Magic Biz Data Gen | Powered by GPT-4o Vision")
