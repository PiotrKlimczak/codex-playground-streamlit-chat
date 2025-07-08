import os

os.environ["CHAT_DB"] = "sqlite:///:memory:"
from app.mcp import apply_mcp
from app.models import Base, engine, SessionLocal, McpTool, User
from app.auth import ensure_user
import streamlit as st


def setup_module(module):
    Base.metadata.create_all(engine)


def test_apply_uppercase():
    assert apply_mcp("hello", ["uppercase"]) == "HELLO"


def test_apply_excited():
    assert apply_mcp("hello", ["excited"]) == "hello!"


def test_apply_multiple():
    assert apply_mcp("hello", ["uppercase", "excited"]) == "HELLO!"


def test_tool_db_interaction(monkeypatch):
    db = SessionLocal()
    user = User(id="u1", email="a@b.com", name="A")
    db.add(user)
    db.commit()

    t1 = McpTool(user_id="u1", name="uppercase", enabled=True)
    t2 = McpTool(user_id="u1", name="excited", enabled=False)
    db.add_all([t1, t2])
    db.commit()

    loaded = db.query(McpTool).filter_by(user_id="u1", name="uppercase").first()
    assert loaded.enabled is True
    db.close()


def test_ensure_user_creates(monkeypatch):
    db = SessionLocal()

    class FakeState(dict):
        pass

    fake = FakeState()
    fake["user"] = {"id": "x", "email": "x@example.com", "name": "X"}
    monkeypatch.setattr(st, "session_state", fake, raising=False)
    user = ensure_user(db)
    assert user.email == "x@example.com"
    assert db.query(User).filter_by(id="x").first() is not None
    db.close()
