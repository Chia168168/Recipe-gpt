# models.py - alternative place to define models (used by some workflows)
from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON

Base = declarative_base()

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
    ingredients = Column(JSON, nullable=False)
    steps = Column(Text, nullable=False)
    baking = Column(JSON, nullable=True)
    timestamp = Column(String(255), default=lambda: datetime.utcnow().isoformat())
    created_at = Column(DateTime, default=datetime.utcnow)
