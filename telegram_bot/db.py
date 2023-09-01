import dataclasses  # Импорт модуля для создания классов данных
import os  # Импорт модуля для работы с операционной системой
import random  # Импорт модуля для работы с генерацией случайных чисел
import time

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

    # Запрос к базе данных для получения непроиндексированных товаров Unas, не содержащих указанные подстроки
    cur.execute("""
        SELECT u.id, u.name, u.code, u.image, u.link, o.id, o.name, o.code, o.image, o.link
        FROM unas u
        JOIN ozon o ON u.id = o.unas_id
        WHERE u.is_edited = FALSE
          AND u.link NOT LIKE ANY (ARRAY['%semena-i-posadochnyy-material%', '%tovary-dlya-otdyha%', '%tovary-dlya-sada%']);
    """)
    records = cur.fetchall()

    if not records:
        conn.close()
        return None, None  # Если нет подходящих записей, вернуть None

    record = random.choice(records)  # Выбор случайной записи из результатов запроса
    unas_item = Item(
        id=record[0], name=record[1], code=record[2], image=record[3], link=record[4]
    )
    ozon_item = Item(
        id=record[5], name=record[6], code=record[7], image=record[8], link=record[9]
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
