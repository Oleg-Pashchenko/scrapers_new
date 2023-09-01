import requests
from bs4 import BeautifulSoup
import dataclasses
import psycopg2
import dotenv
import os

dotenv.load_dotenv()

categories = [
    'semena-i-posadochnyy-material', # не надо
    'tovary-dlya-sada',  # не надо
    'tovary-dlya-doma',  # нужно
    'tovary-dlya-otdyha',  # не нужно
    'tovary-dlya-prazdnika',  # нужно
    'tovary-dlya-zhivotnyh',  # нужно
    'kancelyarskie-tovary'  # нужно
]


@dataclasses.dataclass
class Card:
    name: str
    image: str
    code: int
    link: str


host = 'https://unas.ru'


def main():
    for category in categories:
        page_id = 0
        pages_count = 99999
        while True:
            page_id += 1
            if page_id > pages_count:
                break

            request_url = f'{host}/catalog/{category}/?PAGEN_1={page_id}'
            response = requests.get(url=request_url)
            if response.status_code != 200:
                print('Сервер вернул некорректный ответ!')
                continue

            soup = BeautifulSoup(response.text, features='html.parser')
            pages_count = int(soup.find('div', {'class': 'module-pagination'}).find_all('a')[-1].text)
            print(f"{category}: {page_id} / {pages_count}.")

            items = soup.find_all('div', {'class': 'table-view__item-wrapper'})
            for item in items:
                try:
                    card = Card(
                        name=item.find('img').get('alt').strip(),
                        image=host + item.find('img').get('data-src'),
                        link=host + item.find('a').get('href'),
                        code=int(item.find('a').get('href').split('/')[-2])
                    )
                except Exception as e:
                    print(f'Невозможно создать карточку ({e})')
                    continue

                try:
                    conn = psycopg2.connect(
                        host=os.getenv('DB_HOST'),
                        database=os.getenv('DB_NAME'),
                        user=os.getenv('DB_USER'),
                        password=os.getenv('DB_PASSWORD')
                    )
                    cur = conn.cursor()
                    cur.execute('SELECT * FROM unas WHERE code=%s', (card.code,))
                    record = cur.fetchall()

                    if len(record) != 0:
                        conn.close()
                        continue

                    cur.execute("INSERT INTO unas (name, code, image, link, is_edited) VALUES (%s, %s, %s, %s, %s)",
                                (card.name, card.code, card.image, card.link, False))
                    conn.commit()
                    conn.close()



                except Exception as e:
                    print(f'Невозможно связаться с базой данных ({e})')
                    continue


if __name__ == '__main__':
    main()
