import json

import dotenv
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, \
    ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

import db
from telegram_bot.utils import download_image

dotenv.load_dotenv()
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())


async def delete_prev_message(message: types.Message):
    for i in range(5):
        try:
            await bot.delete_message(message.chat.id, message.message_id - i)
        except:
            pass


async def send_item(message: types.Message):
    await delete_prev_message(message)
    unas_item, ozon_item = db.get_items()
    photos = [
        InputMediaPhoto(open(download_image(unas_item.image, -1), "rb"), caption="Source"),
        InputMediaPhoto(open(download_image(ozon_item.image, 1), "rb"), caption=f"Marketplace{1}")]
    await bot.send_media_group(message.chat.id, media=photos)

    text = f"Источник:\nID: {unas_item.code}\nИмя: {unas_item.name}\n<a href='{unas_item.link}'>Посмотреть товар</a>"
    text += f"\n\nМаркетплейс:\nID: {ozon_item.code}\nИмя: {ozon_item.name}\n<a href='{unas_item.link}'>Посмотреть товар</a>"
    reply_markup = InlineKeyboardMarkup()
    reply_markup.add(
        InlineKeyboardButton(text='✅', callback_data=f'approve_{ozon_item.id}'),
        InlineKeyboardButton(text='❌', callback_data=f'reject_{ozon_item.id}')
    )
    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup, parse_mode="HTML",
                           disable_web_page_preview=True)


@dp.callback_query_handler(lambda data: 'approve' in data.data or 'reject' in data.data)
async def approve_or_reject(data):
    status, ozon_id = data.data.split('_')[0], int(data.data.split('_')[1])
    db.set_status(status, ozon_id)
    await data.answer("Согласовано!")
    await send_item(data.message)

@dp.message_handler(lambda m: m.text == 'Поиск товара' or m.text == 'Попробовать еще раз' or m.text == '/start')
async def item_search_handler(message: types.Message):
    await message.answer(text='Поиск...', reply_markup=ReplyKeyboardRemove())
    await send_item(message)

executor.start_polling(dp)