import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. Конфигурация и стили ---
st.set_page_config(
    page_title="Генерация описаний",
    layout="wide",
    initial_sidebar_state="collapsed"  # Прячем боковую панель по умолчанию
)

# Современный CSS с градиентами, тенями и анимациями
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main { 
        background-color: #f8fafc; 
    }

    /* Стилизация заголовка градиентом */
    .gradient-text {
        background: linear-gradient(90deg, #4F46E5, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: -10px;
        padding-top: 1rem;
    }

    /* Карточки-контейнеры */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #f1f5f9;
    }

    /* Главная кнопка генерации */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.2em; 
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white; 
        border: none;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.39);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
        color: white;
    }

    /* Поля ввода */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background-color: #f8fafc;
        transition: border-color 0.2s;
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus {
        border-color: #4F46E5;
    }

    /* Стилизация вкладок (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 2px solid #f1f5f9;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        color: #4F46E5 !important;
        border-bottom: 2px solid #4F46E5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Инициализация состояния ---
if 'generated_text' not in st.session_state:
    st.session_state.generated_text = ""
if 'show_editor' not in st.session_state:
    st.session_state.show_editor = False

# Заголовок приложения
st.markdown('<h1 class="gradient-text">Генерация описаний</h1>', unsafe_allow_html=True)
st.caption("Платформа интеллектуальной генерации контента")
st.write("")

# --- 3. Навигация через Tabs ---
tab_gen, tab_hist, tab_doc = st.tabs(["Генератор", "История и аналитика", "Документация"])

# --- 4. Вкладка: ГЕНЕРАТОР ---
with tab_gen:
    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        st.markdown("### Настройки товара")

        category = st.selectbox(
            "Выберите категорию",
            ["bags", "bouquets", "jewelry"],
            format_func=lambda x: {"bags": "Сумки", "bouquets": "Букеты", "jewelry": "Ювелирные изделия"}[x]
        )

        attrs = {}
        # Динамические поля сгруппированы визуально
        if category == "bags":
            attrs["name"] = st.text_input("Название модели", "Lady Dior Classic")
            col_a, col_b = st.columns(2)
            with col_a:
                attrs["material"] = st.text_input("Материал", "натуральная кожа")
            with col_b:
                attrs["color"] = st.text_input("Цвет", "угольно-черный")
            attrs["hardware"] = st.text_input("Фурнитура", "золотистый металл")
            attrs["sections"] = st.text_input("Отделения", "два вместительных отдела")

        elif category == "bouquets":
            attrs["flowers"] = st.text_input("Состав", "французские розы и эвкалипт")
            col_a, col_b = st.columns(2)
            with col_a:
                attrs["shades"] = st.text_input("Гамма", "пастельно-розовая")
            with col_b:
                attrs["flower_type"] = st.text_input("Сорт", "премиальные цветы")
            attrs["decor"] = st.text_input("Упаковка", "матовая бумага и ленты")
            attrs["shop_name"] = st.text_input("Бренд", "Elite Flowers")

        elif category == "jewelry":
            attrs["name"] = st.text_input("Модель", "Everlasting")
            col_a, col_b = st.columns(2)
            with col_a:
                attrs["item_type"] = st.text_input("Тип", "кольцо")
            with col_b:
                attrs["material"] = st.text_input("Сплав", "белое золото 585")
            attrs["stone"] = st.text_input("Вставка", "якутский бриллиант")
            attrs["collection"] = st.text_input("Коллекция", "Night Stars")

        st.write("")
        if st.button("Сгенерировать описание"):
            st.session_state.show_editor = False  # Скрываем старый редактор при новой генерации
            try:
                with st.spinner('Нейросеть формирует продающий текст...'):
                    response = requests.post(
                        "http://127.0.0.1:8000/generate",
                        json={"category": category, "attributes": attrs}
                    )
                    if response.status_code == 200:
                        st.session_state.generated_text = response.json()["result"]
                        st.session_state.show_editor = True
                    else:
                        st.error("Ошибка API. Проверьте соединение с сервером.")
            except Exception as e:
                st.error(f"Связь с сервером прервана: {e}")

    with col2:
        st.markdown("### Результат")

        if not st.session_state.generated_text:
            st.info("Заполните характеристики слева и нажмите «Сгенерировать», чтобы получить готовое описание.")

        if st.session_state.show_editor:
            st.success("Успешно сгенерировано")

            # Текст помещен в красивый контейнер, который можно развернуть для редактирования
            with st.expander("Редактировать результат", expanded=True):
                final_text = st.text_area(
                    "Финальный текст",
                    value=st.session_state.generated_text,
                    height=250,
                    label_visibility="collapsed"
                )
                if st.button("Сохранить в базу", key="save_btn"):
                    st.toast("Изменения успешно сохранены")

# --- 5. Вкладка: ИСТОРИЯ ---
with tab_hist:
    st.markdown("### Архив генераций")

    try:
        res = requests.get("http://127.0.0.1:8000/history")
        if res.status_code == 200:
            history_data = res.json()
            if history_data:
                df = pd.DataFrame(history_data)
                df.columns = ["ID", "Категория", "Входные данные", "Текст", "Дата"]
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.download_button(
                    "Скачать CSV",
                    df.to_csv(index=False).encode('utf-8'),
                    "history_export.csv",
                    "text/csv"
                )
            else:
                st.info("В базе данных пока нет записей.")
    except:
        st.error("Не удалось загрузить историю. Убедитесь, что backend-сервер запущен.")

# --- 6. Вкладка: ДОКУМЕНТАЦИЯ ---
with tab_doc:
    st.markdown("### Техническая документация")

    st.markdown("""
    #### Архитектура проекта
    * **Backend:** FastAPI + Jinja2 (система шаблонов)
    * **Database:** SQLite (локальное хранилище данных)
    * **Frontend:** Streamlit с кастомным CSS

    #### Инструкция по масштабированию
    Для интеграции новых товарных матриц обновите словарь `TEMPLATES_LIBRARY` на стороне FastAPI. Фронтенд автоматически подхватит новые категории без необходимости переписывать UI-компоненты.
    """)