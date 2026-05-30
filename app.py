import json
import sqlite3
import random
from datetime import datetime
from typing import Dict, List, Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from jinja2 import Environment, BaseLoader

app = FastAPI(title="E-commerce Content API", version="2.0 (Zero Dependencies)")


# --- 1. Продвинутый кастомный морфологический движок ---
def simple_inflect(phrase: str, case: str) -> str:
    """
    Легковесная функция склонения фраз по базовым правилам.
    Поддерживает множественное число, исключения и защиту от двойного склонения.
    """
    if not phrase:
        return phrase

    words = phrase.split()
    result = []

    # Мини-словарь исключений (Родительный падеж - "из чего?")
    exceptions_gent = {
        # Флористика и текстиль
        "розы": "роз", "ромашки": "ромашек", "лилии": "лилий", "орхидеи": "орхидей",
        "гвоздики": "гвоздик", "герберы": "гербер", "хризантемы": "хризантем",
        "эустомы": "эустом", "альстромерии": "альстромерий", "гортензии": "гортензий",
        "хлопок": "хлопка", "шелк": "шелка", "лён": "льна",
        # Ювелирка и декор (слова мужского рода на мягкий знак)
        "янтарь": "янтаря", "хрусталь": "хрусталя", "жемчуг": "жемчуга"
    }

    for w in words:
        original = w
        w_lower = w.lower()

        # Игнорируем союзы, предлоги и цифры
        if w_lower in ["и", "или", "с", "без", "в", "на", "из", "под"] or w_lower.isdigit():
            result.append(original)
            continue

        # --- ЗАЩИТА ОТ ДВОЙНОГО СКЛОНЕНИЯ ---
        # Если слово УЖЕ в родительном падеже (например, "белого", "золотых", "роз")
        if case == "gent" and (
                w_lower.endswith(('ого', 'его', 'ов', 'ев', 'ых', 'их')) or
                w_lower in exceptions_gent.values()
        ):
            result.append(original)
            continue

        # Если слово УЖЕ в предложном падеже (например, "белом", "оттенках")
        if case == "loct" and w_lower.endswith(('ом', 'ем', 'ах', 'ях')):
            result.append(original)
            continue
        # ------------------------------------

        if case == "gent":  # Родительный (Кого? Чего?)
            # Прилагательные МН. числа
            if w_lower.endswith('ые'):
                w_lower = w_lower[:-2] + 'ых'
            elif w_lower.endswith('ие'):
                w_lower = w_lower[:-2] + 'их'
            # Прилагательные ЕД. числа
            elif w_lower.endswith('ая'):
                w_lower = w_lower[:-2] + 'ой'
            elif w_lower.endswith('яя'):
                w_lower = w_lower[:-2] + 'ей'
            elif w_lower.endswith('ое'):
                w_lower = w_lower[:-2] + 'ого'
            elif w_lower.endswith('ый') or w_lower.endswith('ий') or w_lower.endswith('ой'):
                w_lower = w_lower[:-2] + 'ого'

            # Проверка на слова-исключения
            elif w_lower in exceptions_gent:
                w_lower = exceptions_gent[w_lower]

            # Существительные
            elif w_lower.endswith('ы'):
                w_lower = w_lower[:-1] + 'ов'
            elif w_lower.endswith(('жа', 'ча', 'ша', 'ща')):
                w_lower = w_lower[:-1] + 'и'
            elif w_lower.endswith('а'):
                w_lower = w_lower[:-1] + 'ы'
            elif w_lower.endswith('я'):
                w_lower = w_lower[:-1] + 'и'
            elif w_lower.endswith('о'):
                w_lower = w_lower[:-1] + 'а'
            elif w_lower.endswith('ь'):
                w_lower = w_lower[:-1] + 'и'
            elif w_lower[-1] in 'бвгджзклмнпрстфхцчшщ':
                w_lower = w_lower + 'а'

        elif case == "loct":  # Предложный (О ком? О чем?)
            # Прилагательные
            if w_lower.endswith('ая'):
                w_lower = w_lower[:-2] + 'ой'
            elif w_lower.endswith('яя'):
                w_lower = w_lower[:-2] + 'ей'
            elif w_lower.endswith('ое'):
                w_lower = w_lower[:-2] + 'ом'
            elif w_lower.endswith('ый') or w_lower.endswith('ий') or w_lower.endswith('ой'):
                w_lower = w_lower[:-2] + 'ом'
            # Существительные
            elif w_lower.endswith('а') or w_lower.endswith('я'):
                w_lower = w_lower[:-1] + 'е'
            elif w_lower.endswith('о'):
                w_lower = w_lower[:-1] + 'е'
            elif w_lower[-1] in 'бвгджзклмнпрстфхцчшщ':
                w_lower = w_lower + 'е'

        # Восстанавливаем оригинальный регистр
        if original.istitle():
            result.append(w_lower.capitalize())
        elif original.isupper():
            result.append(w_lower.upper())
        else:
            result.append(w_lower)

    return " ".join(result)


# Настройка среды Jinja2
env = Environment(loader=BaseLoader())
env.filters['gent'] = lambda x: simple_inflect(x, 'gent')
env.filters['loct'] = lambda x: simple_inflect(x, 'loct')

# --- 2. База шаблонов ---
TEMPLATES_LIBRARY = {
    "bags": [
        "Сумка {{ name }} из {{ material | gent }}. "
        "{% if hardware %}Дополнена фурнитурой из {{ hardware | gent }}. {% endif %}"
        "Цвет: {{ color }}. Внутри: {{ sections }}.",

        "Модель {{ name }} ({% if material %}{{ material }}{% else %}эко-материал{% endif %}). "
        "Стильное решение в {{ color | loct }} оттенке. Вместимость: {{ sections }}."
    ],
    "bouquets": [
        "Композиция в {{ shades | loct }} гамме из {{ flowers | gent }}. "
        "{% if flower_type %}Тип: {{ flower_type }}. {% endif %}"
        "Декор: {{ decor }}. С любовью, {{ shop_name }}.",

        "Авторский букет: {{ flowers }}. Основная палитра — {{ shades }}. "
        "Упаковка: {{ decor }}. Создано в {{ shop_name }}."
    ],
    "jewelry": [
        "{{ item_type | capitalize }} «{{ name }}» из {{ material | gent }}. "
        "Вставка: {{ stone }}. {% if collection %}Коллекция: {{ collection }}.{% endif %}",

        "Изящное украшение «{{ name }}». Тип: {{ item_type }}. "
        "Выполнено из {{ material | gent }}. Камень: {{ stone }}."
    ]
}


# --- 3. Модели данных ---
class GenerationRequest(BaseModel):
    category: str = Field(..., example="bags")
    attributes: Dict[str, Any]


class SaveRequest(BaseModel):
    category: str
    attributes: Dict[str, Any]
    final_text: str


class HistoryRecord(BaseModel):
    id: int
    category: str
    input_data: str
    output_text: str
    created_at: str


# --- 4. Инициализация БД (SQLite) ---
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


# --- 5. Сервисная логика (Синонимайзер) ---
def apply_synonyms(text: str) -> str:
    intros = ["Новинка!", "Обратите внимание:", "Хит сезона!", "Рекомендуем:"]
    outros = ["Доступно к заказу.", "Успейте купить!", "Гарантия качества.", "Эксклюзивно."]
    return f"{random.choice(intros)} {text} {random.choice(outros)}"


# --- 6. Эндпоинты API ---
@app.post("/generate", response_description="Генерация текста на основе шаблонов")
async def generate_text(request: GenerationRequest):
    if request.category not in TEMPLATES_LIBRARY:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    try:
        raw_template = random.choice(TEMPLATES_LIBRARY[request.category])
        jinja_template = env.from_string(raw_template)
        rendered_text = jinja_template.render(**request.attributes)
        final_text = apply_synonyms(rendered_text)

        return {"status": "ok", "result": final_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@app.post("/save", response_description="Сохранение результата в базу")
async def save_text(request: SaveRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO generation_history (category, input_data, output_text, created_at) VALUES (?, ?, ?, ?)",
            (request.category, json.dumps(request.attributes, ensure_ascii=False), request.final_text,
             datetime.now().isoformat())
        )
        db.commit()
        return {"status": "ok", "message": "Сохранено успешно"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@app.get("/history", response_model=List[HistoryRecord])
async def get_history(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, category, input_data, output_text, created_at FROM generation_history ORDER BY id DESC"
    )
    rows = cursor.fetchall()

    return [
        HistoryRecord(id=r[0], category=r[1], input_data=r[2], output_text=r[3], created_at=r[4])
        for r in rows
    ]


if __name__ == "__main__":
    import uvicorn

    # Запуск сервера
    uvicorn.run(app, host="127.0.0.1", port=8000)