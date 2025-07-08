# Streamlit LangChain Chat

This example app demonstrates a Streamlit chat interface using LangChain and the OpenAI API. It authenticates with Google OAuth and stores conversations per-user in a local SQLite database.

## Features
- Google authentication (requires a `client_secret.json` OAuth file)
- Dropdown to select from available OpenAI models including `gpt-4o`
- Streaming responses from OpenAI in the chat UI
- Past conversations listed in the sidebar
- Data stored in `chat.db` for each authenticated user

## Quick Start
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Provide a Google OAuth client secret JSON file and set the `GOOGLE_CLIENT_SECRETS_FILE` environment variable to its path.
3. Run the app:
   ```bash
   streamlit run app.py
   ```
