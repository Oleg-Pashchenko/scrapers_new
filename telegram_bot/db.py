import dataclasses  # Импорт модуля для создания классов данных
import os  # Импорт модуля для работы с операционной системой
import random  # Импорт модуля для работы с генерацией случайных чисел
import psycopg2  # Импорт библиотеки для работы с PostgreSQL


@dataclasses.dataclass
class Item:
    id: int
    name: str
    image: str
    code: int
    link: str


# Функция для получения информации о товарах из базы данных
import random
import os
import psycopg2
from typing import Tuple

def get_items() -> Tuple[Item, Item]:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()

    # Запрос к базе данных для получения непроиндексированных товаров Ozon
    cur.execute("SELECT * FROM ozon WHERE is_edited=FALSE;")
    records = cur.fetchall()
    filtered_records = []
    for record in records:
        if 'semena-i-posadochnyy-material' not in record[4] and 'tovary-dlya-otdyha' not in record[4] and 'tovary-dlya-sada' not in record[4]:
            filtered_records.append(record)
    # Фильтрация записей на этапе получения

    if not filtered_records:
        conn.close()
        return None, None  # Если нет подходящих записей, вернуть None

    record = random.choice(filtered_records)  # Выбор случайной записи из отфильтрованных результатов запроса
    ozon_item = Item(
        id=record[0], name=record[2], image=record[3], code=record[4], link=record[5]
    )

    # Запрос к базе данных для получения информации о товаре Unas, связанном с выбранным товаром Ozon
    cur.execute("SELECT * FROM unas WHERE id=%s;", (record[1],))
    record = cur.fetchone()
    unas_item = Item(
        id=record[0], name=record[1], image=record[3], code=record[2], link=record[4]
    )

    conn.close()
    return unas_item, ozon_item


# Функция для установки статуса товара и записи статуса в базу данных
def set_status(status, ozon_id):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )  # Установление соединения с базой данных
    cur = conn.cursor()

    # Обновление статуса товара Ozon в базе данных
    cur.execute("UPDATE ozon SET is_edited = TRUE WHERE id=%s", (ozon_id,))
    conn.commit()

    # Преобразование строки статуса ('approve' или 'reject') в булевое значение
    status = True if status == "approve" else False

    # Запись статуса товара в базу данных
    cur.execute(
        "INSERT INTO human_bot_status (ozon_id, status) VALUES (%s, %s);",
        (
            ozon_id,
            status,
        ),
    )
    conn.commit()

    conn.close()  # Закрытие соединения с базой данных
