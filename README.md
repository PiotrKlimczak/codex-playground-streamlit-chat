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

## MCP Tools
The app supports simple "Model Context Protocol" tools that transform the LLM response.
Each user can enable tools in the sidebar and the selection is stored in the database.
Enabled tools are sent to the OpenAI model using the function-calling API so the model can invoke them during generation.
The example tools included are:

- `uppercase` &ndash; convert the response to upper case
- `excited` &ndash; append an exclamation mark

## Running Tests
Unit tests are located in the `tests` directory and can be run with:
```bash
pytest
```
