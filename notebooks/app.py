import streamlit as st
from forms_agent import FormsAgent, chat_with_agent, DISCLAIMER, History

# 初始化 session state
if "agent" not in st.session_state:
    st.session_state.agent = FormsAgent()
if "history" not in st.session_state:
    st.session_state.history: History = []
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Form Filling Chatbot")

# 顯示 disclaimer
st.info(DISCLAIMER)

# 顯示聊天歷史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "pdf_path" in message:
            with open(message["pdf_path"], "rb") as f:
                st.download_button(
                    label="Download Filled PDF",
                    data=f,
                    file_name="filled_form.pdf",
                    mime="application/pdf"
                )

# 用戶輸入
user_input = st.chat_input("Describe your problem or reply...")

if user_input:
    # 顯示用戶訊息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 呼叫代理
    with st.spinner("Thinking..."):
        reply, st.session_state.history, st.session_state.agent = chat_with_agent(
            user_input, st.session_state.history, st.session_state.agent
        )
    
    # 顯示 AI 回應
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
    
    # 如果有 PDF
    if "Your filled form:" in reply:
        pdf_path = reply.split("Your filled form: ")[1].strip()
        st.session_state.messages[-1]["pdf_path"] = pdf_path
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Download Filled PDF",
                data=f,
                file_name="filled_form.pdf",
                mime="application/pdf",
                key="pdf_download"
            )