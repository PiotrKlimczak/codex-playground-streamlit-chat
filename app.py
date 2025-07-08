import os
from dotenv import load_dotenv
import streamlit as st

from app.db import get_db
from app.auth import google_login, ensure_user
from app.chat import chat_interface

load_dotenv()


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
