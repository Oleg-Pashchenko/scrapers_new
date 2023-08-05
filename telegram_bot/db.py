import dataclasses
import os
import random

import psycopg2


@dataclasses.dataclass
class Item:
    id: int
    name: str
    image: str
    code: int
    link: str


def get_items() -> (Item, Item):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute('SELECT * FROM ozon WHERE is_edited=FALSE;', )
    records = cur.fetchall()
    record = random.choice(records)
    ozon_item = Item(id=record[0], name=record[2], image=record[3], code=record[4], link=record[5])
    cur.execute('SELECT * FROM unas WHERE id=%s;', (record[1],))
    record = cur.fetchone()
    unas_item = Item(id=record[0], name=record[1], image=record[3], code=record[2], link=record[4])
    conn.close()
    return unas_item, ozon_item


def set_status(status, ozon_id):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute('UPDATE ozon SET is_edited = TRUE WHERE id=%s', (ozon_id,))
    conn.commit()
    status = True if status == 'approve' else False
    cur.execute('INSERT INTO human_bot_status (ozon_id, status) VALUES (%s, %s);', (ozon_id, status,))
    conn.commit()
    conn.close()
