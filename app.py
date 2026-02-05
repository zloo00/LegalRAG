# app.py — Streamlit чат для Legal RAG (RU/KZ, дисклеймер, прозрачность AI-закон РК)

import json
import uuid
from datetime import datetime

import streamlit as st

import config
from rag_chain import invoke_qa, validate_answer

CHAT_STORE_PATH = "chat_history.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _load_chats() -> dict:
    try:
        with open(CHAT_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"chats": {}, "order": []}


def _save_chats(store: dict) -> None:
    with open(CHAT_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def _new_chat(store: dict, title: str | None = None) -> str:
    chat_id = str(uuid.uuid4())
    title = title or "Новый чат"
    store["chats"][chat_id] = {
        "id": chat_id,
        "title": title,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "messages": [],
    }
    store["order"].insert(0, chat_id)
    return chat_id


def _rename_chat(store: dict, chat_id: str, title: str) -> None:
    if chat_id in store["chats"]:
        store["chats"][chat_id]["title"] = title.strip() or "Без названия"
        store["chats"][chat_id]["updated_at"] = _now_iso()


def _delete_chat(store: dict, chat_id: str) -> None:
    if chat_id in store["chats"]:
        store["chats"].pop(chat_id, None)
        store["order"] = [cid for cid in store["order"] if cid != chat_id]

# Настройки страницы (должно быть первым вызовом Streamlit)
st.set_page_config(
    page_title="Legal RAG — Помощник по законам РК",
    page_icon="⚖️",
    layout="wide",
)

# Язык интерфейса
if "lang" not in st.session_state:
    st.session_state.lang = "ru"
if "chat_store" not in st.session_state:
    st.session_state.chat_store = _load_chats()
if "current_chat_id" not in st.session_state:
    if not st.session_state.chat_store["order"]:
        st.session_state.current_chat_id = _new_chat(st.session_state.chat_store)
        _save_chats(st.session_state.chat_store)
    else:
        st.session_state.current_chat_id = st.session_state.chat_store["order"][0]

LANG_LABELS = {"ru": "Русский", "kz": "Қазақша"}
DISCLAIMERS = {"ru": config.DISCLAIMER_RU, "kz": config.DISCLAIMER_KZ}
PLACEHOLDERS = {
    "ru": "Задайте вопрос по законам РК (на русском или казахском)",
    "kz": "ҚР заңдары бойынша сұрақ қойыңыз (орыс немесе қазақ тілінде)",
}
SOURCES_LABEL = {"ru": "**Источники (реальные статьи из базы):**", "kz": "**Дереккөздер (базадағы мақалалар):**"}
DOWNLOAD_LABEL = {"ru": "Скачать ответ как TXT", "kz": "Жауапты TXT ретінде жүктеу"}
CLEAR_CHAT = {"ru": "Очистить чат", "kz": "Чатты тазалау"}
NEW_CHAT = {"ru": "Новый чат", "kz": "Жаңа чат"}
DELETE_CHAT = {"ru": "Удалить чат", "kz": "Чатты жою"}
RENAME_CHAT = {"ru": "Переименовать", "kz": "Атауын өзгерту"}
SAVE_CHAT = {"ru": "Сохранить историю", "kz": "Тарихты сақтау"}
INFO_SIDEBAR = {
    "ru": "Задавайте вопросы на русском или казахском. Ответы строго по текстам из Adilet.",
    "kz": "Сұрақтарды орыс немесе қазақ тілінде қойыңыз. Жауаптар тек Adilet мәтіні бойынша.",
}

# Базовый стиль
st.markdown(
    """
<style>
@import url("https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@300;400;600&family=Spectral:wght@400;600&display=swap");

html, body, [class*="stApp"] { font-family: "Source Serif 4", "Spectral", serif; }
.stApp {
  background: linear-gradient(180deg, #f7f3ee 0%, #f2f4f7 55%, #eef1f5 100%);
}
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
}
section[data-testid="stSidebar"] * {
  color: #e5e7eb !important;
}
.title-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 0.25rem;
}
.title-badge {
  font-size: 0.75rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: #0f172a; background: #e2e8f0; padding: 6px 10px; border-radius: 999px;
}
.chat-shell {
  background: rgba(255,255,255,0.75);
  border: 1px solid rgba(15,23,42,0.12);
  border-radius: 16px;
  padding: 12px;
}
.stChatMessage {
  border-radius: 12px;
}
</style>
    """,
    unsafe_allow_html=True,
)

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
    st.markdown(f"Модель: {config.LLM_MODEL}")
    st.markdown(f"Эмбеддинги: {config.EMBEDDING_MODEL}")
    st.divider()
    if st.button(NEW_CHAT[st.session_state.lang], key="new_chat"):
        new_id = _new_chat(st.session_state.chat_store)
        st.session_state.current_chat_id = new_id
        _save_chats(st.session_state.chat_store)
        st.rerun()

    # Список чатов
    chat_titles = [
        (cid, st.session_state.chat_store["chats"][cid]["title"])
        for cid in st.session_state.chat_store["order"]
        if cid in st.session_state.chat_store["chats"]
    ]
    if chat_titles:
        selected = st.radio(
            "Чаты",
            options=[cid for cid, _ in chat_titles],
            format_func=lambda cid: next(t for c, t in chat_titles if c == cid),
            index=0,
            key="chat_selector",
        )
        st.session_state.current_chat_id = selected

    st.divider()
    if st.button(DELETE_CHAT[st.session_state.lang], key="delete_chat"):
        current_id = st.session_state.current_chat_id
        _delete_chat(st.session_state.chat_store, current_id)
        if not st.session_state.chat_store["order"]:
            st.session_state.current_chat_id = _new_chat(st.session_state.chat_store)
        else:
            st.session_state.current_chat_id = st.session_state.chat_store["order"][0]
        _save_chats(st.session_state.chat_store)
        st.rerun()

    new_title = st.text_input(RENAME_CHAT[st.session_state.lang], value="", key="rename_input")
    if st.button(RENAME_CHAT[st.session_state.lang] + " ✓", key="rename_btn") and new_title.strip():
        _rename_chat(st.session_state.chat_store, st.session_state.current_chat_id, new_title)
        _save_chats(st.session_state.chat_store)
        st.rerun()

    st.info(INFO_SIDEBAR[st.session_state.lang])

# Заголовок и дисклеймер (на выбранном языке)
st.markdown(
    """
<div class="title-bar">
  <div class="title-badge">LEGAL RAG</div>
  <h1>Помощник по законам Республики Казахстан</h1>
</div>
    """,
    unsafe_allow_html=True,
)
st.warning(DISCLAIMERS[st.session_state.lang])

# Соответствие закону РК об ИИ (прозрачность)
st.caption(config.AI_LAW_COMPLIANCE_NOTE)

# История чата
current_chat = st.session_state.chat_store["chats"][st.session_state.current_chat_id]
messages = current_chat["messages"]
st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
st.markdown("</div>", unsafe_allow_html=True)

# Ввод вопроса
prompt = st.chat_input(PLACEHOLDERS[st.session_state.lang])
if prompt:
    messages.append({"role": "user", "content": prompt})
    current_chat["updated_at"] = _now_iso()
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Ищу в текстах законов..." if st.session_state.lang == "ru" else "Заң мәтінінде іздеймін..."):
        try:
            result = invoke_qa(prompt)
            response = result["result"]
            sources = result["source_documents"]
            response = validate_answer(prompt, response, sources)
            if response == "Информация не найдена в доступных текстах законов.":
                sources = []
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
    messages.append({"role": "assistant", "content": response})
    current_chat["updated_at"] = _now_iso()
    _save_chats(st.session_state.chat_store)

if len(messages) > 2 and st.button(CLEAR_CHAT[st.session_state.lang] + " (тек осы чат)", key="clear_chat"):
    current_chat["messages"] = []
    current_chat["updated_at"] = _now_iso()
    _save_chats(st.session_state.chat_store)
    st.rerun()
