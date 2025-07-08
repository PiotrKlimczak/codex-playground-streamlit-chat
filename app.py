import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from sqlalchemy import (create_engine, Column, Integer, String, Text, ForeignKey,
                        DateTime)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("CHAT_DB", "sqlite:///chat.db")
CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE", "client_secret.json")

# Database setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    conversations = relationship("Conversation", back_populates="user")

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

Base.metadata.create_all(bind=engine)

AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4",
    "gpt-3.5-turbo"
]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def google_login():
    redirect_uri = st.session_state.get("redirect_uri")
    if not redirect_uri:
        redirect_uri = st.experimental_get_url()
        st.session_state["redirect_uri"] = redirect_uri

    if "credentials" not in st.session_state:
        params = st.experimental_get_query_params()
        if "code" in params:
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=[
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "openid",
                ],
                state=st.session_state.get("oauth_state"),
                redirect_uri=redirect_uri,
            )
            flow.fetch_token(authorization_response=st.experimental_get_url())
            credentials = flow.credentials
            idinfo = id_token.verify_oauth2_token(
                credentials._id_token,
                Request(),
                flow.client_config["client_id"],
            )
            st.session_state["credentials"] = credentials
            st.session_state["user"] = {
                "email": idinfo.get("email"),
                "id": idinfo.get("sub"),
                "name": idinfo.get("name", "")
            }
        else:
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=[
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "openid",
                ],
                redirect_uri=redirect_uri,
            )
            authorization_url, state = flow.authorization_url(prompt="consent")
            st.session_state["oauth_state"] = state
            st.markdown(f"[Login with Google]({authorization_url})")
            st.stop()


def ensure_user(db):
    user_info = st.session_state.get("user")
    if not user_info:
        return None
    user = db.query(User).filter(User.id == user_info["id"]).first()
    if not user:
        user = User(id=user_info["id"], email=user_info["email"], name=user_info["name"])
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def sidebar(db, user):
    st.sidebar.title("Chats")
    if st.sidebar.button("New Chat"):
        conv = Conversation(user_id=user.id)
        db.add(conv)
        db.commit()
        st.session_state["conversation_id"] = conv.id
        st.session_state["messages"] = []
    conversations = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.created_at.desc()).all()
    for conv in conversations:
        if st.sidebar.button(conv.title, key=f"conv_{conv.id}"):
            st.session_state["conversation_id"] = conv.id
            st.session_state["messages"] = [
                {"role": m.role, "content": m.content}
                for m in conv.messages
            ]

    model = st.sidebar.selectbox("Model", AVAILABLE_MODELS)
    st.session_state["model"] = model


def chat_interface(db, user):
    sidebar(db, user)
    st.title("Chat with OpenAI")
    messages = st.session_state.get("messages", [])
    for m in messages:
        if m["role"] == "user":
            st.chat_message("user").write(m["content"])
        else:
            st.chat_message("assistant").write(m["content"])

    if prompt := st.chat_input("Message..."):
        messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            response_container = st.empty()
            all_text = ""
            chat = ChatOpenAI(model=st.session_state.get("model", AVAILABLE_MODELS[0]), streaming=True)
            for chunk in chat.stream([
                HumanMessage(content=prompt)
            ]):
                all_text += chunk.content
                response_container.write(all_text)
            messages.append({"role": "assistant", "content": all_text})

        # Persist to DB
        conversation_id = st.session_state.get("conversation_id")
        if not conversation_id:
            conv = Conversation(user_id=user.id)
            db.add(conv)
            db.commit()
            conversation_id = conv.id
            st.session_state["conversation_id"] = conv.id
        db.add(Message(conversation_id=conversation_id, role="user", content=prompt))
        db.add(Message(conversation_id=conversation_id, role="assistant", content=all_text))
        db.commit()

        st.session_state["messages"] = messages


def main():
    for db in get_db():
        google_login()
        user = ensure_user(db)
        if user:
            chat_interface(db, user)
        else:
            st.stop()


if __name__ == "__main__":
    main()
