#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import qrcode
from PIL import Image
import io
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

creds_json = st.secrets["gcp_service_account_json"]
creds_dict = json.loads(creds_json)

scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# スプレッドシートのURLを追加する
SHEET_URL = "https://docs.google.com/spreadsheets/d/1LqLxGOx6YcAdB9WLqvPP8qutF7br1YNp4WyVKzambqE/edit"
sheet = client.open_by_url(SHEET_URL)

# 「設定」シートからパスワードを取得
settings_worksheet = sheet.worksheet("設定")
settings_data = settings_worksheet.get_all_records()
SECRET_PASSWORD = str(settings_data[0]["値"])

# 「項目」シートから入力フォームの項目リストを取得
items_worksheet = sheet.worksheet("項目")
items_data = items_worksheet.get_all_records()

# システムの見出し
st.title("SBRC 入室管理QR発行ツール")

# パスワード入力欄
user_password = st.text_input("合言葉を入力してください", type="password")

if user_password == SECRET_PASSWORD:
    st.success("認証成功！")
    
    with st.form("qr_form"):
        # QRに埋め込むベースのデータ
        user_inputs = {"facility": "KKK"}
        
        # スプレッドシートの「項目」シートに従って入力欄を自動生成
        for item in items_data:
            item_name = item["項目名"]
            item_type = item["種類"]
            
            if item_type == "テキスト":
                user_inputs[item_name] = st.text_input(f"{item_name}（必須）")
            elif item_type == "プルダウン":
                # カンマ区切りの選択肢をリスト（配列）に変換
                options = ["選択してください"] + item["選択肢"].split(",")
                user_inputs[item_name] = st.selectbox(f"{item_name}", options)
        
        submitted = st.form_submit_button("QRコードを作成")

    if submitted:
        # 未入力や「選択してください」のままの項目がないかチェック
        if any(val == "" or val == "選択してください" for val in user_inputs.values()):
            st.error("すべての項目を正しく入力してください。")
        else:
            # 入力データに現在時刻を追加
            user_inputs["issued_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # JSON形式の文字データに変換
            qr_string = json.dumps(user_inputs, ensure_ascii=False)
            
            # QRコードの生成処理
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.image(byte_im, caption=f"入出管理QRコード")
            
            st.download_button(
                label="Download",
                data=byte_im,
                file_name=f"Visiter_QR.png",
                mime="image/png"
            )
elif user_password != "":
    st.error("password error")