import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request

from .models import User

CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE", "client_secret.json")


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
                "name": idinfo.get("name", ""),
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
