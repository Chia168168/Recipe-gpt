# import_from_sheets.py
import os
import json
import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
from models import Base, Recipe  # 從你的 repo 引入 Recipe model

from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SPREADSHEET_ID = os.getenv("SHEET_ID")  # 你的 Google Sheet ID
RANGE_NAME = "工作表1!A:L"               # 資料範圍，請依實際表格調整
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DB SETUP ---
engine = sqlalchemy.create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(bind=engine))
Base.metadata.create_all(bind=engine)

# --- GOOGLE SHEETS ---
# 用 Service Account JSON（credentials.json）認證
creds = service_account.Credentials.from_service_account_file(
    "credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

def import_data():
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    if not values:
        print("❌ 試算表沒有資料")
        return

    headers = values[0]
    rows = values[1:]
    grouped = {}

    for row in rows:
        data = dict(zip(headers, row))
        title = data.get("食譜名稱") or "未命名"
        group = data.get("分組", "")
        ing = {
            "group": group,
            "name": data.get("食材", ""),
            "weight": float(data.get("重量") or 0),
            "percent": data.get("百分比", ""),
            "desc": data.get("說明", "")
        }
        steps = data.get("步驟", "")
        baking = {
            "topHeat": data.get("上火溫度", ""),
            "bottomHeat": data.get("下火溫度", ""),
            "time": data.get("烘烤時間", ""),
            "convection": data.get("旋風", "") in ["是", "true", "True", "1"],
            "steam": data.get("蒸汽", "") in ["是", "true", "True", "1"],
        }
        timestamp = data.get("建立時間") or datetime.utcnow().isoformat()

        if title not in grouped:
            grouped[title] = {"ingredients": [], "steps": steps, "baking": baking, "timestamp": timestamp}
        grouped[title]["ingredients"].append(ing)

    db = SessionLocal()
    try:
        for title, rec in grouped.items():
            exists = db.query(Recipe).filter(Recipe.title == title).one_or_none()
            if exists:
                print(f"⚠️ 已存在，跳過：{title}")
                continue
            recipe = Recipe(
                title=title,
                ingredients=rec["ingredients"],
                steps=rec["steps"],
                baking=rec["baking"],
                timestamp=rec["timestamp"]
            )
            db.add(recipe)
            print(f"✅ 匯入成功：{title}")
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    import_data()
