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
import dotenv

dotenv.load_dotenv()


def get_items() -> (Item, Item):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )  # Установление соединения с базой данных
    cur = conn.cursor()

    # Запрос к базе данных для получения непроиндексированных товаров Ozon
    cur.execute("SELECT * FROM ozon WHERE is_edited=FALSE;")
    records = cur.fetchall()
    record = random.choice(records)  # Выбор случайной записи из результатов запроса
    ozon_item = Item(
        id=record[0], name=record[2], image=record[3], code=record[4], link=record[5]
    )

    # Запрос к базе данных для получения информации о товаре Unas, связанном с выбранным товаром Ozon
    cur.execute("SELECT * FROM unas WHERE id=%s;", (record[1],))
    record = cur.fetchone()
    unas_item = Item(
        id=record[0], name=record[1], image=record[3], code=record[2], link=record[4]
    )
    conn.close()  # Закрытие соединения с базой данных
    if 'semena-i-posadochnyy-material' in unas_item.link or\
            'tovary-dlya-sada' in unas_item.link or 'tovary-dlya-otdyha' in unas_item.link:
        return get_items()
    return unas_item, ozon_item  # Возвращение пары товаров


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


get_items()
