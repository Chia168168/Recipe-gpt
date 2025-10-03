# app.py - Flask backend for TENG 食譜系統 (converted from Google Apps Script)
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL") or os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # allow sqlite fallback for easy local testing
    DATABASE_URL = "sqlite:///teng_recipes.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

# Models
class IngredientDB(Base):
    __tablename__ = "ingredients_db"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    hydration = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True)
    title = Column(String(1024), unique=True, nullable=False)
    ingredients = Column(JSON, nullable=False)  # list of ingredient dicts
    steps = Column(Text, nullable=False)
    baking = Column(JSON, nullable=True)
    timestamp = Column(String(255), default=lambda: datetime.utcnow().isoformat())
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = Flask(__name__, template_folder="templates", static_folder="templates")

# Serve frontend
@app.route("/")
def index():
    return render_template("index.html")

# Ingredient endpoints
@app.route("/api/ingredients", methods=["GET"])
def get_ingredients():
    db = SessionLocal()
    try:
        rows = db.query(IngredientDB).order_by(IngredientDB.name).all()
        out = [{"name": r.name, "hydration": r.hydration} for r in rows]
        return jsonify(out)
    finally:
        db.close()

@app.route("/api/ingredients", methods=["POST"])
def save_ingredient():
    db = SessionLocal()
    try:
        payload = request.get_json()
        name = payload.get("name")
        hydration = float(payload.get("hydration", 0) or 0)
        if not name:
            return jsonify({"message": "必須提供 name"}), 400
        inst = db.query(IngredientDB).filter(IngredientDB.name==name).one_or_none()
        if inst:
            inst.hydration = hydration
            db.add(inst)
            msg = "已更新自訂食材"
        else:
            inst = IngredientDB(name=name, hydration=hydration)
            db.add(inst)
            msg = "已新增自訂食材"
        db.commit()
        return jsonify({"message": msg})
    finally:
        db.close()

@app.route("/api/ingredients/<string:name>", methods=["DELETE"])
def delete_ingredient(name):
    db = SessionLocal()
    try:
        inst = db.query(IngredientDB).filter(IngredientDB.name==name).one_or_none()
        if not inst:
            return jsonify({"message": "找不到指定食材"}), 404
        db.delete(inst)
        db.commit()
        return jsonify({"message": f"已刪除 {name}"})
    finally:
        db.close()

# Recipe endpoints
@app.route("/api/recipes", methods=["GET"])
def get_recipes():
    db = SessionLocal()
    try:
        rows = db.query(Recipe).order_by(Recipe.created_at.desc()).all()
        out = []
        for r in rows:
            out.append({
                "title": r.title,
                "ingredients": r.ingredients,
                "steps": r.steps,
                "baking": r.baking or {},
                "timestamp": r.timestamp
            })
        return jsonify(out)
    finally:
        db.close()

@app.route("/api/recipes", methods=["POST"])
def save_recipe():
    db = SessionLocal()
    try:
        payload = request.get_json()
        title = payload.get("title")
        ingredients = payload.get("ingredients")
        steps = payload.get("steps")
        baking = payload.get("baking", {})

        if not title or not steps or not ingredients:
            return jsonify({"message": "請完整填寫食譜名稱、步驟與至少一個食材"}), 400

        exists = db.query(Recipe).filter(Recipe.title==title).one_or_none()
        if exists:
            return jsonify({"message": "同名食譜已存在，若要更新請使用 PUT"}), 400

        r = Recipe(
            title=title,
            ingredients=ingredients,
            steps=steps,
            baking=baking,
            timestamp=datetime.utcnow().isoformat()
        )
        db.add(r)
        db.commit()
        return jsonify({"message": "食譜已儲存"})
    finally:
        db.close()

@app.route("/api/recipes/<string:title>", methods=["PUT"])
def update_recipe(title):
    db = SessionLocal()
    try:
        payload = request.get_json()
        new_title = payload.get("title")
        ingredients = payload.get("ingredients")
        steps = payload.get("steps")
        baking = payload.get("baking", {})

        r = db.query(Recipe).filter(Recipe.title==title).one_or_none()
        if not r:
            return jsonify({"message": "找不到要更新的食譜"}), 404

        r.title = new_title or r.title
        r.ingredients = ingredients or r.ingredients
        r.steps = steps or r.steps
        r.baking = baking or r.baking
        r.timestamp = datetime.utcnow().isoformat()
        db.add(r)
        db.commit()
        return jsonify({"message": "食譜已更新"})
    finally:
        db.close()

@app.route("/api/recipes/<string:title>", methods=["DELETE"])
def delete_recipe(title):
    db = SessionLocal()
    try:
        r = db.query(Recipe).filter(Recipe.title==title).one_or_none()
        if not r:
            return jsonify({"message": "找不到指定食譜"}), 404
        db.delete(r)
        db.commit()
        return jsonify({"message": f"已刪除 {title}"})
    finally:
        db.close()

# Diagnose / Fix / Clear endpoints (ported from code.gs)
@app.route("/api/diagnose", methods=["GET"])
def diagnose():
    db = SessionLocal()
    try:
        ing_count = db.query(IngredientDB).count()
        rec_count = db.query(Recipe).count()
        return jsonify({"ingredients_count": ing_count, "recipes_count": rec_count})
    finally:
        db.close()

@app.route("/api/clear", methods=["POST"])
def clear_all():
    db = SessionLocal()
    try:
        db.query(Recipe).delete()
        db.query(IngredientDB).delete()
        db.commit()
        return jsonify({"message":"已清除所有數據"})
    finally:
        db.close()

@app.route("/api/fix", methods=["POST"])
def fix_data():
    # Placeholder - implement any needed data fixes here.
    return jsonify({"message":"沒有需要修復的資料結構"})

# Legacy import: accept CSV export of Google Sheet with the expected columns and convert to recipes
@app.route("/api/import_legacy_csv", methods=["POST"])
def import_legacy_csv():
    """
    Accepts a file upload (form-data) named 'file' which is a CSV export of the original Google Sheet.
    The expected headers (in Chinese) are:
    食譜名稱, 分組, 食材, 重量 (g), 百分比, 說明, 步驟, 建立時間, 上火溫度, 下火溫度, 烘烤時間, 旋風, 蒸汽
    This will group rows by recipe title and assemble ingredients into JSON, then store as Recipe entries.
    """
    if 'file' not in request.files:
        return jsonify({"message":"請上傳 CSV 檔案（form-data field name='file'）"}), 400
    f = request.files['file']
    content = f.read().decode('utf-8')
    import csv, io
    reader = csv.DictReader(io.StringIO(content))
    groups = {}
    baking_map = {}
    timestamp_map = {}
    for row in reader:
        title = row.get('食譜名稱') or row.get('title') or row.get('Title') or '未命名'
        group = row.get('分組','')
        name = row.get('食材','')
        weight = row.get('重量 (g)','0') or row.get('重量','0') or '0'
        percent = row.get('百分比','') or row.get('percent','')
        desc = row.get('說明','') or row.get('desc','')
        steps = row.get('步驟','') or row.get('steps','')
        timestamp = row.get('建立時間') or datetime.utcnow().isoformat()
        top = row.get('上火溫度','')
        bottom = row.get('下火溫度','')
        timeb = row.get('烘烤時間','')
        convection = row.get('旋風','') in ['是','True','true','1']
        steam = row.get('蒸汽','') in ['是','True','true','1']
        ing = {
            "group": group,
            "name": name,
            "weight": float(weight) if weight else 0,
            "percent": percent,
            "desc": desc
        }
        if title not in groups:
            groups[title] = []
            baking_map[title] = {"topHeat": top, "bottomHeat": bottom, "time": timeb, "convection": convection, "steam": steam}
            timestamp_map[title] = timestamp
        groups[title].append(ing)
    # store into DB
    db = SessionLocal()
    try:
        added = 0
        for title, ings in groups.items():
            exists = db.query(Recipe).filter(Recipe.title==title).one_or_none()
            if exists:
                # skip or update? We'll skip to avoid overwriting
                continue
            r = Recipe(title=title, ingredients=ings, steps=steps or "", baking=baking_map.get(title, {}), timestamp=timestamp_map.get(title))
            db.add(r)
            added += 1
        db.commit()
        return jsonify({"message":f"已匯入 {added} 個食譜（跳過同名食譜）"})
    finally:
        db.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
