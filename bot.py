import os
import asyncio
import logging
import aiohttp
from datetime import datetime
from aiohttp import web
from aiohttp.web import Request
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

TOKEN = os.getenv('BOT_TOKEN')
GSHEETS_URL = os.getenv('GSHEETS_URL')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 8000))

if not TOKEN:
    raise ValueError('BOT_TOKEN не установлен в переменных окружения')
if not GSHEETS_URL:
    raise ValueError('GSHEETS_URL не установлен в переменных окружения')

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Keep-alive система
class KeepAliveSystem:
    def __init__(self):
        self.ping_count = 0
        self.is_running = True
        self.start_time = datetime.now()
    
    async def start_keep_alive(self):
        """Запуск системы поддержания активности"""
        logger.info("🔄 Запуск keep-alive системы")
        
        while self.is_running:
            try:
                await asyncio.sleep(600)  # 10 минут
                await self.perform_ping()
            except Exception as e:
                logger.error(f"❌ Ошибка keep-alive: {e}")
    
    async def perform_ping(self):
        """Выполнение пинга для поддержания активности"""
        self.ping_count += 1
        current_time = datetime.now()
        
        try:
            if WEBHOOK_URL:
                url = f"{WEBHOOK_URL}/health"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as response:
                        logger.info(f"🏓 Keep-alive ping #{self.ping_count}: {response.status} в {current_time.strftime('%H:%M:%S')}")
            else:
                logger.info(f"🏓 Keep-alive ping #{self.ping_count} в {current_time.strftime('%H:%M:%S')} (локальный режим)")
                
        except Exception as e:
            logger.error(f"❌ Ping failed: {e}")
    
    def get_uptime(self):
        """Получить время работы бота"""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
    
    def stop(self):
        """Остановка keep-alive системы"""
        self.is_running = False
        logger.info("🛑 Keep-alive система остановлена")

# Глобальный экземпляр keep-alive
keep_alive = KeepAliveSystem()

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

# Улучшенный обработчик команды start
@dp.message(Command("start"))
async def start(message: types.Message):
    logger.info(f"👤 Команда /start от пользователя {message.from_user.id} ({message.from_user.full_name})")
    await message.answer(
        "🚀 Добро пожаловать! Я помогу автоматизировать ваш бизнес.\n"
        "Выберите действие:",
        reply_markup=main_menu
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    logger.info(f"❓ Команда /help от пользователя {message.from_user.id}")
    await message.answer(
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "/start - Запустить бота\n"
        "/help - Показать справку\n"
        "/status - Статус бота\n"
        "/ping - Проверка связи\n\n"
        "Используйте кнопки меню для навигации.",
        parse_mode="HTML",
        reply_markup=main_menu
    )

# Улучшенный обработчик команды status с дополнительной информацией
@dp.message(Command("status"))
async def status_command(message: types.Message):
    logger.info(f"📊 Команда /status от пользователя {message.from_user.id} ({message.from_user.full_name})")
    
    # Получаем информацию о webhook
    try:
        webhook_info = await bot.get_webhook_info()
        webhook_status = "🟢 Активен" if webhook_info.url else "🔴 Не установлен"
        webhook_url_display = webhook_info.url if webhook_info.url else "Не установлен"
    except Exception as e:
        webhook_status = f"⚠️ Ошибка: {str(e)[:50]}"
        webhook_url_display = "Недоступно"
    
    # Формируем сообщение со статусом
    status_message = (
        f"✅ <b>Статус бота:</b>\n\n"
        f"🤖 <b>ID бота:</b> {bot.id}\n"
        f"👤 <b>Ваш ID:</b> {message.from_user.id}\n"
        f"🌐 <b>Сервер:</b> {'Heroku' if WEBHOOK_URL else 'Local'}\n"
        f"🔄 <b>Режим:</b> {'Webhook' if WEBHOOK_URL else 'Polling'}\n"
        f"📡 <b>Webhook:</b> {webhook_status}\n"
        f"📊 <b>Состояние:</b> Активен\n"
        f"⏱️ <b>Время работы:</b> {keep_alive.get_uptime()}\n"
        f"🏓 <b>Keep-alive пингов:</b> {keep_alive.ping_count}\n"
        f"⏰ <b>Текущее время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"🕐 <b>Время запуска:</b> {keep_alive.start_time.strftime('%d.%m.%Y %H:%M:%S')}"
    )
    
    await message.answer(status_message, parse_mode="HTML")

# Новая команда для быстрой проверки связи
@dp.message(Command("ping"))
async def ping_command(message: types.Message):
    logger.info(f"🏓 Команда /ping от пользователя {message.from_user.id}")
    start_time = datetime.now()
    
    sent_message = await message.answer("🏓 Понг!")
    
    # Вычисляем время отклика
    response_time = (datetime.now() - start_time).total_seconds() * 1000
    
    await sent_message.edit_text(
        f"🏓 <b>Понг!</b>\n\n"
        f"⚡ Время отклика: {response_time:.0f}мс\n"
        f"🤖 Бот работает исправно\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}",
        parse_mode="HTML"
    )

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
        "🔗 GitHub: https://github.com/JustProject174/JustProject_174.git\n"
        "📹 Видео-демо: youtu.be/demo\n"
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

                if response.status in [200, 302]:
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
            "📱 Telegram: @JProj_174\n"
            "📧 Email: Projman174@yandex.ru",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении заказа: {e}", exc_info=True)
        await callback.answer("⚠ Произошла ошибка", show_alert=True)
        await callback.message.edit_text(
            f"⚠️ <b>Ошибка при оформлении заказа</b>\n\n"
            f"Техническая информация: {str(e)[:100]}...\n\n"
            "Пожалуйста, свяжитесь со мной напрямую:\n"
            "📱 Telegram: @JProj_174\n"
            "📧 Email: Projman174@yandex.ru\n\n"
            "Мы обязательно поможем вам!",
            parse_mode="HTML"
        )

# Остальные обработчики сообщений остаются без изменений...
@dp.message(F.text.lower().contains("цена") | F.text.lower().contains("стоимость") | F.text.lower().contains("сколько"))
async def price_question(message: types.Message):
    await message.answer(
        "💰 <b>Цены на мои услуги:</b>\n\n"
        "📊 Парсинг данных — от 3 000₽\n"
        "📋 Автоматизация Excel — от 1 000₽\n"
        "🤖 Telegram-бот — от 8 000₽\n"
        "💬 Консультация — бесплатно\n\n"
        "💡 <i>Итоговая стоимость зависит от сложности проекта.\n"
        "Для точной оценки нужно обсудить техническое задание.</i>\n\n"
        "🛒 Хотите заказать? Нажмите кнопку ниже!",
        parse_mode="HTML",
        reply_markup=main_menu
    )

# Обработчик для отладки - показывает все входящие сообщения
@dp.message(F.text.startswith("/"))
async def debug_commands(message: types.Message):
    """Отладочный обработчик для всех команд"""
    logger.info(f"🔧 Получена команда: {message.text} от пользователя {message.from_user.id}")
    
    # Если команда не обработана другими хендлерами
    if message.text not in ["/start", "/help", "/status", "/ping"]:
        await message.answer(
            f"❓ <b>Неизвестная команда:</b> <code>{message.text}</code>\n\n"
            "📋 <b>Доступные команды:</b>\n"
            "/start - Запустить бота\n"
            "/help - Показать справку\n"
            "/status - Статус бота\n"
            "/ping - Проверка связи\n\n"
            "Используйте кнопки меню для навигации.",
            parse_mode="HTML",
            reply_markup=main_menu
        )

@dp.message()
async def handle_unknown_message(message: types.Message):
    logger.info(f"📝 Неизвестное сообщение: '{message.text}' от пользователя {message.from_user.id}")
    await message.answer(
        "🤔 Я не понимаю это сообщение.\n\n"
        "Воспользуйтесь кнопками меню ниже или командами:\n"
        "/help - справка по командам",
        reply_markup=main_menu
    )

async def webhook_handler(request: Request):
    """Обработчик webhook от Telegram"""
    try:
        data = await request.json()
        logger.info(f"📨 Получен webhook: {data.get('update_id', 'unknown')}")
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Ошибка webhook: {e}", exc_info=True)
        return web.Response(status=500, text="Error")

async def health_check(request: Request):
    """Проверка состояния приложения с keep-alive информацией"""
    current_time = datetime.now()
    uptime_info = f"Bot is running! Time: {current_time.strftime('%d.%m.%Y %H:%M:%S')}, Keep-alive pings: {keep_alive.ping_count}, Uptime: {keep_alive.get_uptime()}"
    
    logger.info(f"🏥 Health check: {uptime_info}")
    return web.Response(text=uptime_info, content_type="text/plain")

async def setup_webhook():
    """Настройка webhook для Heroku"""
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook установлен: {webhook_url}")
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📊 Статус webhook: {webhook_info}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
        raise

@dp.error()
async def error_handler(event: types.ErrorEvent):
    logger.error(f"Критическая ошибка: {event.exception}", exc_info=True)

    if hasattr(event, 'update') and event.update.callback_query:
        try:
            await event.update.callback_query.answer(
                "⚠️ Произошла техническая ошибка. Попробуйте позже.",
                show_alert=True
            )
        except Exception:
            pass

    elif hasattr(event, 'update') and event.update.message:
        try:
            await event.update.message.answer(
                "⚠️ Произошла техническая ошибка.\n"
                "Попробуйте позже или свяжитесь с администратором.",
                reply_markup=main_menu
            )
        except Exception:
            pass

async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск Telegram-бота на Heroku с keep-alive системой...")

    # Получаем информацию о боте при запуске
    try:
        bot_info = await bot.get_me()
        logger.info(f"🤖 Информация о боте: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о боте: {e}")

    try:
        if WEBHOOK_URL:
            logger.info("🌐 Режим работы: Webhook")
            await setup_webhook()
            
            # Создаем aiohttp приложение
            app = web.Application()
            app.router.add_post('/webhook', webhook_handler)
            app.router.add_get('/health', health_check)
            
            # Запускаем keep-alive систему в фоне
            asyncio.create_task(keep_alive.start_keep_alive())
            
            # Настраиваем runner
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', PORT)
            
            logger.info(f"🖥 Сервер запущен на порту {PORT}")
            await site.start()
            
            # Бесконечный цикл для поддержания работы
            while True:
                await asyncio.sleep(3600)  # 1 час
        else:
            logger.info("💻 Режим работы: Polling")
            await bot.delete_webhook(drop_pending_updates=True)
            
            # Запускаем keep-alive систему в фоне (для локального тестирования)
            asyncio.create_task(keep_alive.start_keep_alive())
            
            await dp.start_polling(bot)
            
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка при запуске: {e}", exc_info=True)
    finally:
        keep_alive.stop()
        await bot.session.close()
        logger.info("🛑 Бот остановлен")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Принудительная остановка бота")
    except Exception as e:
        logger.critical(f"❌ Необработанное исключение: {e}", exc_info=True)
