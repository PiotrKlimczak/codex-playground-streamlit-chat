import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, ToolMessage

from .models import Conversation, Message, McpTool
from .mcp import apply_mcp, TOOLS, TOOL_SCHEMAS, handle_tool_calls

AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4",
    "gpt-3.5-turbo",
]


def get_or_create_tools(db, user):
    tools = {t.name: t for t in db.query(McpTool).filter_by(user_id=user.id).all()}
    updated = False
    for name in TOOLS.keys():
        if name not in tools:
            tool = McpTool(user_id=user.id, name=name, enabled=False)
            db.add(tool)
            updated = True
    if updated:
        db.commit()
    return {t.name: t for t in db.query(McpTool).filter_by(user_id=user.id).all()}


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

    tools = get_or_create_tools(db, user)
    enabled_names = []
    for name, tool in tools.items():
        val = st.sidebar.checkbox(f"Enable {name}", value=tool.enabled)
        if val != tool.enabled:
            tool.enabled = val
            db.commit()
        if val:
            enabled_names.append(name)
    st.session_state["mcp_tools"] = enabled_names


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
            llm = ChatOpenAI(model=st.session_state.get("model", AVAILABLE_MODELS[0]), streaming=True)
            enabled = st.session_state.get("mcp_tools", [])
            schemas = [TOOL_SCHEMAS[n] for n in enabled]
            chunks = llm.stream([
                HumanMessage(content=prompt)
            ], tools=schemas, tool_choice="auto")
            for chunk in chunks:
                # handle tool calls if the model emits them
                tool_calls = chunk.additional_kwargs.get("tool_calls")
                if tool_calls:
                    tool_msgs = handle_tool_calls(tool_calls)
                    follow_up = llm.invoke([
                        HumanMessage(content=prompt),
                        *tool_msgs,
                    ], tools=schemas, tool_choice="none")
                    all_text += follow_up.content
                    break
                else:
                    all_text += chunk.content
                    response_container.write(all_text)
            all_text = apply_mcp(all_text, enabled)
            messages.append({"role": "assistant", "content": all_text})

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
