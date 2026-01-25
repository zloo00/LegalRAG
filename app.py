# app.py — Streamlit чат для Legal RAG

import streamlit as st
from rag_chain import qa_chain  # твоя qa_chain из rag_chain.py

# Настройки страницы
st.set_page_config(
    page_title="Legal RAG — Помощник по законам РК",
    page_icon="⚖️",
    layout="wide"
)

# Заголовок и дисклеймер
st.title("Legal RAG — Помощник по законам Республики Казахстан")
st.warning("""
Это **не официальная юридическая консультация** и **не заменяет адвоката**.  
Информация основана исключительно на текстах законов из официальных источников (Adilet).  
Всегда проверяйте актуальные редакции на adilet.zan.kz.
""")

# Инициализация истории чата
if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода вопроса
if prompt := st.chat_input("Задайте вопрос по законам РК (на русском или казахском)"):
    # Добавляем сообщение пользователя
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Показываем "думает..."
    with st.spinner("Ищу в текстах законов..."):
        try:
            result = qa_chain.invoke({"query": prompt})
            response = result["result"]
            sources = result["source_documents"]
        except Exception as e:
            response = f"Ошибка при обработке вопроса: {str(e)}"
            sources = []

    # Вывод ответа
    with st.chat_message("assistant"):
        st.markdown(response)

        if sources:
            st.markdown("**Источники (реальные статьи из базы):**")
            for i, doc in enumerate(sources, 1):
                source = doc.metadata.get('source', 'неизвестно')
                # Убираем путь, оставляем только имя файла
                filename = source.split('/')[-1]
                preview = doc.page_content[:280].replace('\n', ' ').strip()
                st.markdown(f"{i}. **{filename}** — {preview}...")

        # Кнопка очистки чата (внизу ответа)
        if st.button("Очистить чат", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    # Сохраняем ответ в историю
    st.session_state.messages.append({"role": "assistant", "content": response})

# Кнопка очистки чата (если история длинная)
if len(st.session_state.messages) > 2 and st.button("Очистить весь чат"):
    st.session_state.messages = []
    st.rerun()