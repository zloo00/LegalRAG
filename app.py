import streamlit as st
from rag_chain import qa_chain  # импортируй твою qa_chain

st.title("Legal RAG — Помощник по законам РК")

st.warning("Это не официальная юридическая консультация. Только информация из текстов законов.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Задайте вопрос по законам РК"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Ищу в законах..."):
        result = qa_chain.invoke({"query": prompt})
        response = result["result"]
        sources = result["source_documents"]

    with st.chat_message("assistant"):
        st.markdown(response)
        if sources:
            st.markdown("**Источники:**")
            for i, doc in enumerate(sources, 1):
                source = doc.metadata.get('source', 'неизвестно')
                preview = doc.page_content[:200].replace('\n', ' ')
                st.markdown(f"{i}. {source} — {preview}...")

    st.session_state.messages.append({"role": "assistant", "content": response})