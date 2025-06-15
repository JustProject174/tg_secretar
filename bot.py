import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import aiohttp
from aiogram import F
from aiohttp import web
from aiohttp.web_request import Request


TOKEN = os.getenv('BOT_TOKEN')
GSHEETS_URL = os.getenv('GSHEETS_URL')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 8000))


if not TOKEN:
    raise ValueError('BOT_TOKEN не установлен в переменных окружения')
if not GSHEETS_URL:
    raise ValueError('GSHEETS_URL не установлен в переменных окружения')

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ========================
# ГЛАВНОЕ МЕНЮ
# ========================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Услуги")],
        [KeyboardButton(text="🖥 Портфолио")],
        [KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="🛒 Заказать")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)


# ========================
# ОБРАБОТЧИКИ КОМАНД
# ========================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🚀 Добро пожаловать! Я помогу автоматизировать ваш бизнес.\n"
        "Выберите действие:",
        reply_markup=main_menu
    )


@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "/start - Запустить бота\n"
        "/help - Показать справку\n"
        "/status - Статус бота\n\n"
        "Используйте кнопки меню для навигации.",
        parse_mode="HTML",
        reply_markup=main_menu
    )


@dp.message(Command("status"))
async def status_command(message: types.Message):
    await message.answer(
        "✅ <b>Статус бота:</b>\n\n"
        "🌐 Сервер: Heroku\n"
        "🔄 Режим: Webhook\n"
        "📊 Состояние: Активен\n"
        "🕐 Время работы: 24/7",
        parse_mode="HTML"
    )


# ========================
# ОБРАБОТЧИКИ КНОПОК
# ========================
@dp.message(F.text == "📊 Услуги")
async def show_services(message: types.Message):
    await message.answer(
        "💰 <b>Мои услуги и цены:</b>\n\n"
        "📊 Парсинг данных — от 3 000₽\n"
        "   • Сбор данных с сайтов\n"
        "   • Обработка больших объемов\n"
        "   • Регулярное обновление\n\n"
        "📋 Автоматизация Excel — от 1 000₽\n"
        "   • Макросы и формулы\n"
        "   • Автоотчеты\n"
        "   • Интеграция с системами\n\n"
        "🤖 Telegram-бот — от 8 000₽\n"
        "   • Индивидуальная разработка\n"
        "   • Интеграция с API\n"
        "   • Техподдержка\n\n"
        "📝 <i>Каждый проект индивидуален, цена может варьироваться в зависимости от сложности.</i>",
        parse_mode="HTML"
    )


@dp.message(F.text == "🖥 Портфолио")
async def show_portfolio(message: types.Message):
    await message.answer(
        "📂 <b>Мои работы:</b>\n\n"
        "🔗 GitHub: github.com/your_profile\n"
        "📹 Видео-демо: youtu.be/demo\n"
        "💼 LinkedIn: linkedin.com/in/yourprofile\n\n"
        "🏆 <b>Выполненные проекты:</b>\n"
        "• 50+ ботов для автоматизации\n"
        "• 30+ парсеров данных\n"
        "• 20+ Excel автоматизаций\n\n"
        "⭐ Средняя оценка: 4.9/5\n"
        "🔍 <i>Примеры работ и отзывы доступны по ссылкам выше.</i>",
        parse_mode="HTML"
    )


@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: types.Message):
    await message.answer(
        "📞 <b>Как со мной связаться:</b>\n\n"
        "📱 Telegram: @JProj_174\n"
        "📧 Email: Projman174@yandex.ru\n"
        "🌐 Сайт: yourwebsite.com\n"
        "⏰ Часы работы: 10:00-18:00 МСК\n\n"
        "⚡ <b>Время ответа:</b>\n"
        "• В рабочие часы: 1-2 часа\n"
        "• Вне рабочих часов: до 8 часов\n"
        "• Выходные: до 24 часов\n\n"
        "💬 <i>Предпочитаю общение в Telegram для быстрых ответов</i>",
        parse_mode="HTML"
    )


# ========================
# СИСТЕМА ЗАКАЗОВ
# ========================
@dp.message(F.text == "🛒 Заказать")
async def start_order(message: types.Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Парсинг данных (от 3 000₽)", callback_data="order_parse")],
            [InlineKeyboardButton(text="📋 Автоматизация Excel (от 1 000₽)", callback_data="order_excel")],
            [InlineKeyboardButton(text="🤖 Разработка бота (от 8 000₽)", callback_data="order_bot")],
            [InlineKeyboardButton(text="💬 Консультация (бесплатно)", callback_data="order_consultation")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
        ]
    )
    await message.answer(
        "🔍 <b>Выберите услугу для заказа:</b>\n\n"
        "После выбора я свяжусь с вами для уточнения деталей и составления технического задания.",
        reply_markup=inline_kb,
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "cancel_order")
async def cancel_order(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "❌ <b>Заказ отменен</b>\n\n"
        "Если передумаете, всегда можете вернуться через главное меню!",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("order_"))
async def process_order(callback: types.CallbackQuery):
    service_map = {
        "order_parse": ("Парсинг данных", 3000, "📊"),
        "order_excel": ("Автоматизация Excel", 1000, "📋"),
        "order_bot": ("Разработка бота", 8000, "🤖"),
        "order_consultation": ("Консультация", 0, "💬")
    }

    if callback.data not in service_map:
        await callback.answer("❌ Услуга не найдена!", show_alert=True)
        return

    service, price, emoji = service_map[callback.data]

    # Подготавливаем данные для отправки
    order_data = {
        "client_name": callback.from_user.full_name or "Не указано",
        "client_id": str(callback.from_user.id),
        "service": service,
        "price": price,
        "status": "Новый",
        "username": callback.from_user.username or "Не указан",
        "comment": f"Заказ через Telegram-бота в {callback.message.date}"
    }

    logger.info(f"Обработка заказа: {service} для пользователя {callback.from_user.id}")

    # Сохраняем в Google Sheets
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    GSHEETS_URL,
                    json=order_data,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                response_text = await response.text()
                logger.info(f"Google Sheets ответ: {response.status} - {response_text}")

                if response.status in [200, 302]:  # 302 - нормальный редирект для GAS
                    await callback.answer("✅ Заказ успешно оформлен!", show_alert=False)

                    price_text = f"от {price:,}₽" if price > 0 else "Бесплатно"

                    await callback.message.edit_text(
                        f"{emoji} <b>Заказ оформлен!</b>\n\n"
                        f"👤 <b>Клиент:</b> {order_data['client_name']}\n"
                        f"🔧 <b>Услуга:</b> {service}\n"
                        f"💰 <b>Стоимость:</b> {price_text}\n"
                        f"📅 <b>Дата:</b> {callback.message.date.strftime('%d.%m.%Y %H:%M')}\n\n"
                        f"📞 <b>Что дальше?</b>\n"
                        f"Я свяжусь с вами в течение часа для:\n"
                        f"• Уточнения требований\n"
                        f"• Составления ТЗ\n"
                        f"• Согласования сроков\n\n"
                        f"🙏 Спасибо за выбор наших услуг!",
                        parse_mode="HTML"
                    )
                else:
                    logger.error(f"Неожиданный статус от Google Sheets: {response.status}")
                    raise aiohttp.ClientError(f"HTTP {response.status}")

    except asyncio.TimeoutError:
        logger.error("Таймаут при отправке в Google Sheets")
        await callback.answer("⚠ Превышено время ожидания", show_alert=True)
        await callback.message.edit_text(
            "⚠️ <b>Временные проблемы с сервером</b>\n\n"
            "Заказ не был сохранен автоматически.\n"
            "Пожалуйста, свяжитесь со мной напрямую:\n\n"
            "📱 Telegram: @your_username\n"
            "📧 Email: your@email.com",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении заказа: {e}", exc_info=True)
        await callback.answer("⚠ Произошла ошибка", show_alert=True)
        await callback.message.edit_text(
            f"⚠️ <b>Ошибка при оформлении заказа</b>\n\n"
            f"Техническая информация: {str(e)[:100]}...\n\n"
            "Пожалуйста, свяжитесь со мной напрямую:\n"
            "📱 Telegram: @your_username\n"
            "📧 Email: your@email.com\n\n"
            "Мы обязательно поможем вам!",
            parse_mode="HTML"
        )


# ========================
# ОБРАБОТКА НЕИЗВЕСТНЫХ СООБЩЕНИЙ
# ========================
@dp.message()
async def handle_unknown_message(message: types.Message):
    await message.answer(
        "🤔 Я не понимаю это сообщение.\n\n"
        "Воспользуйтесь кнопками меню ниже или командами:\n"
        "/help - справка по командам",
        reply_markup=main_menu
    )


# ========================
# WEBHOOK ОБРАБОТЧИК
# ========================
async def webhook_handler(request: Request):
    """Обработчик webhook от Telegram"""
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Ошибка webhook: {e}", exc_info=True)
        return web.Response(status=500, text="Error")


async def health_check(request: Request):
    """Проверка здоровья приложения"""
    return web.Response(text="Bot is running!", content_type="text/plain")


# ========================
# НАСТРОЙКА WEBHOOK
# ========================
async def setup_webhook():
    """Настройка webhook для Heroku"""
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"

        # Удаляем старый webhook
        await bot.delete_webhook(drop_pending_updates=True)

        # Устанавливаем новый webhook
        await bot.set_webhook(webhook_url)

        logger.info(f"✅ Webhook установлен: {webhook_url}")

        # Проверяем статус webhook
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📊 Статус webhook: {webhook_info}")

    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
        raise


# ========================
# ОБРАБОТКА ОШИБОК
# ========================
@dp.error()
async def error_handler(event: types.ErrorEvent):
    logger.error(f"Критическая ошибка: {event.exception}", exc_info=True)

    # Если ошибка произошла в callback query
    if hasattr(event, 'update') and event.update.callback_query:
        try:
            await event.update.callback_query.answer(
                "⚠ Произошла техническая ошибка. Попробуйте позже.",
                show_alert=True
            )
        except Exception:
            pass

    # Если ошибка произошла в обычном сообщении
    elif hasattr(event, 'update') and event.update.message:
        try:
            await event.update.message.answer(
                "⚠️ Произошла техническая ошибка.\n"
                "Попробуйте позже или свяжитесь с администратором.",
                reply_markup=main_menu
            )
        except Exception:
            pass


# ========================
# ГЛАВНАЯ ФУНКЦИЯ
# ========================
async def main():
    logger.info("🚀 Запуск Telegram-бота на Heroku...")

    try:
        if WEBHOOK_URL:
            # Режим webhook для продакшена (Heroku)
            logger.info("🌐 Запуск в режиме webhook")

            await setup_webhook()

            # Создаем веб-приложение
            app = web.Application()
            app.router.add_post('/webhook', webhook_handler)
            app.router.add_get('/health', health_check)
            app.router.add_get('/', health_check)  # Для проверки Heroku

            # Запускаем сервер
            runner = web.AppRunner(app)
            await runner.setup()

            site = web.TCPSite(runner, '0.0.0.0', PORT)
            await site.start()

            logger.info(f"✅ Webhook сервер запущен на порту {PORT}")
            logger.info(f"🔗 Health check: {WEBHOOK_URL}/health")

            # Держим приложение запущенным
            while True:
                await asyncio.sleep(3600)  # Проверяем каждый час

        else:
            # Режим polling для разработки
            logger.info("🔄 Запуск в режиме polling (разработка)")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, skip_updates=True)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка запуска: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)