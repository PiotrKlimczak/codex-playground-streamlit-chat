import os
import datetime
from sqlalchemy import (create_engine, Column, Integer, String, Text, ForeignKey,
                        DateTime, Boolean)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.environ.get("CHAT_DB", "sqlite:///chat.db")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    conversations = relationship("Conversation", back_populates="user")
    tools = relationship("McpTool", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    messages = relationship("Message", back_populates="conversation")
    user = relationship("User", back_populates="conversations")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")

class McpTool(Base):
    __tablename__ = "mcp_tools"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    enabled = Column(Boolean, default=False)
    user = relationship("User", back_populates="tools")

Base.metadata.create_all(bind=engine)
