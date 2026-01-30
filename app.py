# app.py — Streamlit чат для Legal RAG (RU/KZ, дисклеймер, прозрачность AI-закон РК)

import streamlit as st
import config
from rag_chain import qa_chain

# Настройки страницы (должно быть первым вызовом Streamlit)
st.set_page_config(
    page_title="Legal RAG — Помощник по законам РК",
    page_icon="⚖️",
    layout="wide",
)

# Язык интерфейса
if "lang" not in st.session_state:
    st.session_state.lang = "ru"
if "messages" not in st.session_state:
    st.session_state.messages = []

LANG_LABELS = {"ru": "Русский", "kz": "Қазақша"}
DISCLAIMERS = {"ru": config.DISCLAIMER_RU, "kz": config.DISCLAIMER_KZ}
PLACEHOLDERS = {
    "ru": "Задайте вопрос по законам РК (на русском или казахском)",
    "kz": "ҚР заңдары бойынша сұрақ қойыңыз (орыс немесе қазақ тілінде)",
}
SOURCES_LABEL = {"ru": "**Источники (реальные статьи из базы):**", "kz": "**Дереккөздер (базадағы мақалалар):**"}
DOWNLOAD_LABEL = {"ru": "Скачать ответ как TXT", "kz": "Жауапты TXT ретінде жүктеу"}
CLEAR_CHAT = {"ru": "Очистить чат", "kz": "Чатты тазалау"}
INFO_SIDEBAR = {
    "ru": "Задавайте вопросы на русском или казахском. Ответы строго по текстам из Adilet.",
    "kz": "Сұрақтарды орыс немесе қазақ тілінде қойыңыз. Жауаптар тек Adilet мәтіні бойынша.",
}

# Сайдбар: язык и настройки
with st.sidebar:
    st.header("Legal RAG")
    st.markdown("Помощник по законам РК" if st.session_state.lang == "ru" else "ҚР заңдары бойынша көмекші")
    lang = st.radio(
        "Язык интерфейса / Интерфейс тілі",
        options=["ru", "kz"],
        format_func=lambda x: LANG_LABELS[x],
        index=0 if st.session_state.lang == "ru" else 1,
        key="lang_radio",
    )
    st.session_state.lang = lang
    st.divider()
    st.markdown("База: 12 кодексов, 5643+ чанков")
    st.markdown(f"Модель: {config.LLM_MODEL} (локально)")
    st.markdown(f"Эмбеддинги: {config.EMBEDDING_MODEL}")
    st.divider()
    if st.button(CLEAR_CHAT[st.session_state.lang], key="sidebar_clear"):
        st.session_state.messages = []
        st.rerun()
    st.info(INFO_SIDEBAR[st.session_state.lang])

# Заголовок и дисклеймер (на выбранном языке)
st.title("Legal RAG — Помощник по законам Республики Казахстан")
st.warning(DISCLAIMERS[st.session_state.lang])

# Соответствие закону РК об ИИ (прозрачность)
st.caption(config.AI_LAW_COMPLIANCE_NOTE)

# История чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод вопроса
prompt = st.chat_input(PLACEHOLDERS[st.session_state.lang])
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Ищу в текстах законов..." if st.session_state.lang == "ru" else "Заң мәтінінде іздеймін..."):
        try:
            result = qa_chain.invoke({"query": prompt})
            response = result["result"]
            sources = result["source_documents"]
        except Exception as e:
            response = f"Ошибка при обработке вопроса: {str(e)}"
            sources = []

    with st.chat_message("assistant"):
        st.markdown(response)
        if sources:
            st.markdown(SOURCES_LABEL[st.session_state.lang])
            for i, doc in enumerate(sources, 1):
                src = doc.metadata.get("source", "неизвестно")
                filename = src.split("/")[-1] if "/" in src else src
                code_ru = doc.metadata.get("code_ru", "")
                art = doc.metadata.get("article_number", "")
                preview = doc.page_content[:280].replace("\n", " ").strip()
                st.markdown(f"{i}. **{filename}**" + (f" — {code_ru} ст.{art}" if art else "") + f" — {preview}...")
    if sources:
        sources_text = "\n".join([
            f"{j + 1}. {doc.metadata.get('source', '')} — {doc.metadata.get('code_ru', '')} ст.{doc.metadata.get('article_number', '')} — {doc.page_content[:200].replace(chr(10), ' ')}..."
            for j, doc in enumerate(sources)
        ])
        full_text = f"{response}\n\nИсточники:\n{sources_text}"
        st.download_button(
            label=DOWNLOAD_LABEL[st.session_state.lang],
            data=full_text,
            file_name="ответ_по_законам.txt",
            mime="text/plain",
        )
    st.session_state.messages.append({"role": "assistant", "content": response})

if len(st.session_state.messages) > 2 and st.button(CLEAR_CHAT[st.session_state.lang] + " (все)", key="clear_all"):
    st.session_state.messages = []
    st.rerun()
