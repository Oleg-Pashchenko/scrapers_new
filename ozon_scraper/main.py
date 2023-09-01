import os  # Импорт модуля для работы с операционной системой
import bs4  # Импорт BeautifulSoup для разбора HTML
import psycopg2  # Импорт библиотеки для работы с PostgreSQL
import time  # Импорт модуля для управления временем
import dotenv  # Импорт библиотеки для загрузки переменных окружения из файла .env
import dataclasses  # Импорт модуля для создания классов данных

from bs4 import BeautifulSoup  # Импорт BeautifulSoup для разбора HTML
from selenium import webdriver  # Импорт библиотеки Selenium для веб-автоматизации
from selenium.webdriver.chrome.options import Options  # Импорт настроек браузера Chrome


@dataclasses.dataclass
class Card:
    id: int
    name: str
    image: str
    code: int
    link: str


dotenv.load_dotenv()  # Загрузка переменных окружения из файла .env


# Функция для выбора карточки товара для обработки
def select_card() -> Card | None:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM unas WHERE is_edited = FALSE;")
    record = cur.fetchone()
    if record is None:
        return None
    card = Card(
        id=record[0], name=record[1], image=record[3], code=record[2], link=record[4]
    )
    cur.close()
    conn.close()
    return card


# Функция для парсинга данных с веб-сайта Ozon
def scrape(source_item: Card):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(
            f"https://www.ozon.ru/search/?text={source_item.name}&from_global=true"
        )
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, features="html.parser")
        driver.quit()
        items = (
            soup.find("div", {"data-widget": "searchResultsV2"})
            .find_next("div")
            .find_all_next("div")
        )
        ozon_items = []
        codes = []
        for item in items:
            try:
                name = item.find("span", {"class": "tsBody500Medium"}).text
                ozon_item_link_el = item.findNext("a")
                if not ozon_item_link_el:
                    continue
                ozon_item_link = "https://www.ozon.ru" + ozon_item_link_el.get("href")
                ozon_id = ozon_item_link.split("/?")[0].split("-")[-1]
                if (
                    ozon_id == "https://www.ozon.ruhttps://job.ozon.ru/"
                    or ozon_item_link_el.find("img") is None
                ):
                    continue
                img = ozon_item_link_el.find("img").get("src")
                card = Card(
                    code=int(ozon_id), image=img, name=name, link=ozon_item_link, id=0
                )
                if card.code not in codes:
                    codes.append(card.code)
                    ozon_items.append(card)
            except Exception as e:
                pass
        driver.quit()
    except Exception as e:
        ozon_items = []
    return ozon_items[:3]


# Функция для загрузки данных о товаре Ozon в базу данных
def upload_ozon_card(ozon_card: Card, unas_id: int):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ozon (unas_id, name, image, code, link) VALUES (%s, %s, %s, %s, %s);",
        (
            unas_id,
            ozon_card.name,
            ozon_card.image,
            ozon_card.code,
            ozon_card.link,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


# Функция для обновления флага is_edited в базе данных Unas
def update_unas_card(unas_card_id: int):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute("UPDATE unas SET is_edited = TRUE WHERE id=%s;", (unas_card_id,))
    conn.commit()
    cur.close()
    conn.close()


# Основная функция, выполняющая обработку товаров
def main():
    while True:
        card: Card = select_card()
        if card is None:
            time.sleep(60)  # Если нет карточек для обработки, ожидать 60 секунд
        ozon_cards: list[Card] = scrape(card)
        for ozon_card in ozon_cards:
            upload_ozon_card(ozon_card, card.id)
        update_unas_card(card.id)


if __name__ == "__main__":
    main()
