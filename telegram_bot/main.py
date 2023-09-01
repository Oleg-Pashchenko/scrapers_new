import json  # Импорт модуля для работы с JSON

import dotenv  # Импорт библиотеки для загрузки переменных окружения из файла .env
import os  # Импорт модуля для работы с операционной системой
from aiogram import (
    Bot,
    Dispatcher,
    types,
)  # Импорт библиотеки aiogram для создания бота Telegram
from aiogram.contrib.fsm_storage.memory import (
    MemoryStorage,
)  # Импорт хранилища состояний в памяти
from aiogram.types import (
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    ReplyKeyboardMarkup,
    KeyboardButton,
)  # Импорт типов сообщений и клавиатур для Telegram
from aiogram.utils import executor  # Импорт утилит для запуска бота

import db  # Импорт модуля для работы с базой данных
from utils import download_image  # Импорт функции для загрузки изображений

dotenv.load_dotenv()  # Загрузка переменных окружения из файла .env
bot = Bot(
    token=os.getenv("TELEGRAM_BOT_TOKEN")
)  # Создание объекта бота с использованием токена
dp = Dispatcher(
    bot, storage=MemoryStorage()
)  # Создание диспетчера с использованием хранилища в памяти


# Функция для удаления предыдущих сообщений
async def delete_prev_message(message: types.Message):
    for i in range(5):
        try:
            await bot.delete_message(message.chat.id, message.message_id - i)
        except:
            pass


# Функция для отправки информации о товаре
async def send_item(message: types.Message):
    await delete_prev_message(message)  # Удаление предыдущих сообщений
    (
        unas_item,
        ozon_item,
    ) = db.get_items()  # Получение информации о товарах из базы данных

    # Создание списка медиа-файлов (изображений) для отправки
    photos = [
        InputMediaPhoto(
            open(download_image(unas_item.image, -1), "rb"), caption="Source"
        ),
        InputMediaPhoto(
            open(download_image(ozon_item.image, 1), "rb"), caption=f"Marketplace{1}"
        ),
    ]

    # Отправка группы медиа-файлов с подписями
    await bot.send_media_group(message.chat.id, media=photos)

    # Формирование текста сообщения с информацией о товарах и ссылками
    text = f"Источник:\nID: {unas_item.code}\nИмя: {unas_item.name}\n<a href='{unas_item.link}'>Посмотреть товар</a>"
    text += f"\n\nМаркетплейс:\nID: {ozon_item.code}\nИмя: {ozon_item.name}\n<a href='{ozon_item.link}'>Посмотреть товар</a>"

    # Создание кнопок для согласования или отклонения товара
    reply_markup = InlineKeyboardMarkup()
    reply_markup.add(
        InlineKeyboardButton(text="✅", callback_data=f"approve_{ozon_item.id}"),
        InlineKeyboardButton(text="❌", callback_data=f"reject_{ozon_item.id}"),
    )

    # Отправка сообщения с информацией и кнопками
    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# Обработчик колбэков (нажатия кнопок)
@dp.callback_query_handler(lambda data: "approve" in data.data or "reject" in data.data)
async def approve_or_reject(data):
    status, ozon_id = data.data.split("_")[0], int(data.data.split("_")[1])
    db.set_status(status, ozon_id)  # Обновление статуса товара в базе данных
    await data.answer("Согласовано!")  # Отправка ответа на колбэк
    await send_item(data.message)  # Отправка информации о следующем товаре


# Обработчик текстовых сообщений
@dp.message_handler(
    lambda m: m.text == "Поиск товара"
    or m.text == "Попробовать еще раз"
    or m.text == "/start"
)
async def item_search_handler(message: types.Message):
    await message.answer(
        text="Поиск...", reply_markup=ReplyKeyboardRemove()
    )  # Отправка сообщения о начале поиска
    await send_item(message)  # Отправка информации о товаре


# Запуск бота
executor.start_polling(dp)
