import json
import sqlite3
import random
from datetime import datetime
from typing import Dict, List, Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from jinja2 import Template

app = FastAPI(title="AI Content Generator API", version="1.5.0")

# --- 1. Продвинутая база шаблонов (используем синтаксис Jinja2) ---
# Это позволяет делать проверку: если атрибут пустой, текст про него не выводится.
TEMPLATES_LIBRARY = {
    "bags": [
        "Сумка {{ name }} из материала {{ material }}. "
        "{% if hardware %}Дополнена {{ hardware }} фурнитурой. {% endif %}"
        "Цвет: {{ color }}. Внутри {{ sections }}.",

        "Модель {{ name }} ({% if material %}{{ material }}{% else %}эко-материал{% endif %}). "
        "Стильное решение в оттенке {{ color }}. Вместимость: {{ sections }}."
    ],
    "bouquets": [
        "Композиция '{{ shades }}' из {{ flowers }}. "
        "{% if flower_type %}Тип: {{ flower_type }}. {% endif %}"
        "Декор: {{ decor }}. С любовью, {{ shop_name }}.",

        "Авторский букет: {{ flowers }}. Основная палитра — {{ shades }}. "
        "Упаковка: {{ decor }}. Создано в {{ shop_name }}."
    ],
    "jewelry": [
        "{{ item_type | capitalize }} '{{ name }}' из {{ material }}. "
        "Вставка: {{ stone }}. {% if collection %}Коллекция: {{ collection }}.{% endif %}",

        "Изящное украшение {{ name }}. Тип: {{ item_type }}. "
        "Материал: {{ material }}. Камень: {{ stone }}."
    ]
}


# --- 2. Модели данных ---
class GenerationRequest(BaseModel):
    category: str = Field(
        ...,
        example="bags")
    attributes: Dict[str, Any]


class HistoryRecord(BaseModel):
    id: int
    category: str
    input_data: str
    output_text: str
    created_at: str


# --- 3. Инициализация БД (SQLite) ---
def get_db():
    conn = sqlite3.connect('app_data.db', check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

@app.on_event("startup")
def startup_db():
    conn = sqlite3.connect('app_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            input_data TEXT,
            output_text TEXT,
            created_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()


# --- 4. Сервисная логика (Синонимайзер) ---
def apply_synonyms(text: str) -> str:
    intros = ["Новинка!", "Обратите внимание:", "Хит сезона!", "Рекомендуем:"]
    outros = ["Доступно к заказу.", "Успейте купить!", "Гарантия качества.", "Эксклюзивно."]
    return f"{random.choice(intros)} {text} {random.choice(outros)}"


# --- 5. Эндпоинты API ---

@app.post("/generate", response_description="Генерация текста на основе шаблонов")
async def generate_text(request: GenerationRequest, db: sqlite3.Connection = Depends(get_db)):
    if request.category not in TEMPLATES_LIBRARY:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    try:
        # 1. Выбор случайного шаблона
        raw_template = random.choice(TEMPLATES_LIBRARY[request.category])

        # 2. Рендеринг через Jinja2 (усложнение для логики внутри текста)
        jinja_template = Template(raw_template)
        rendered_text = jinja_template.render(**request.attributes)

        # 3. Применение синонимов
        final_text = apply_synonyms(rendered_text)

        # 4. Сохранение в историю (Спринт 3)
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO generation_history (category, input_data, output_text, created_at) VALUES (?, ?, ?, ?)",
            (request.category, json.dumps(request.attributes, ensure_ascii=False), final_text,
             datetime.now().isoformat())
        )
        db.commit()

        return {"status": "ok", "result": final_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@app.get("/history", response_model=List[HistoryRecord])
async def get_history(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, category, input_data, output_text, created_at FROM generation_history ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()

    return [
        HistoryRecord(id=r[0], category=r[1], input_data=r[2], output_text=r[3], created_at=r[4])
        for r in rows
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)