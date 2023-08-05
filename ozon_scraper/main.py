import os

import bs4
import psycopg2
import time
import dotenv
import dataclasses

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@dataclasses.dataclass
class Card:
    id: int
    name: str
    image: str
    code: int
    link: str


dotenv.load_dotenv()


def select_card() -> Card | None:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute('SELECT * FROM unas WHERE is_edited = FALSE;')
    record = cur.fetchone()
    if record is None:
        return None
    card = Card(id=record[0], name=record[1], image=record[3], code=record[2], link=record[4])
    cur.close()
    conn.close()
    return card


def scrape(source_item: Card):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"https://www.ozon.ru/search/?text={source_item.name}&from_global=true")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, features="html.parser")
        driver.quit()
        items = soup.find("div", {"data-widget": "searchResultsV2"}).find_next("div").find_all_next("div")
        ozon_items = []
        codes = []
        for item in items:
            try:
                name = item.find('span', {'class': 'tsBody500Medium'}).text
                ozon_item_link_el = item.findNext("a")
                if not ozon_item_link_el:
                    continue
                ozon_item_link = "https://www.ozon.ru" + ozon_item_link_el.get("href")
                ozon_id = ozon_item_link.split("/?")[0].split("-")[-1]
                if ozon_id == 'https://www.ozon.ruhttps://job.ozon.ru/' or ozon_item_link_el.find("img") is None:
                    continue
                img = ozon_item_link_el.find("img").get("src")
                card = Card(code=int(ozon_id), image=img, name=name, link=ozon_item_link, id=0)
                if card.code not in codes:
                    codes.append(card.code)
                    ozon_items.append(card)
            except Exception as e:
                pass
        driver.quit()
    except Exception as e:
        ozon_items = []
    return ozon_items[:3]


def upload_ozon_card(ozon_card: Card, unas_id: int):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute('INSERT INTO ozon (unas_id, name, image, code, link) VALUES (%s, %s, %s, %s, %s);',
                (unas_id, ozon_card.name, ozon_card.image, ozon_card.code, ozon_card.link,))
    conn.commit()
    cur.close()
    conn.close()


def update_unas_card(unas_card_id: int):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute('UPDATE unas SET is_edited = TRUE WHERE id=%s;', (unas_card_id,))
    conn.commit()
    cur.close()
    conn.close()


def main():
    while True:
        card: Card = select_card()
        if card is None:
            time.sleep(60)
        ozon_cards: list[Card] = scrape(card)
        for ozon_card in ozon_cards:
            upload_ozon_card(ozon_card, card.id)
        update_unas_card(card.id)


if __name__ == '__main__':
    main()
