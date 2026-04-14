"""
Главный цикл бота - мониторинг чата VK через Playwright + трекинг зрителей
"""
import asyncio
import time
import os
import sys

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from playwright.async_api import async_playwright
from chatbot.constants import (
    CHAT_PAGE_URL, BOT_PAGE_LOAD_WAIT, BOT_POLL_INTERVAL,
    BOT_CACHE_LIMIT, BOT_CACHE_CLEANUP, BOT_ERROR_WAIT,
    CHROME_PROFILE_PATH, DEBOUNCE_SECONDS
)

from chatbot.bot.bot_Handler import process_message
from chatbot.utils.bot_utils import delete_message_via_api


async def viewer_poll_task(tracker):
    """Фоновая задача для опроса зрителей каждые 5 минут"""
    print("[ViewerPoll] Starting background viewer polling...")
    
    while True:
        try:
            await tracker.process_viewer_poll()
            await asyncio.sleep(tracker.poll_interval)  # 5 минут
        except Exception as e:
            print(f"[ViewerPoll] Error: {e}")
            await asyncio.sleep(60)  # Подождать минуту при ошибке


async def bot_task():
    """Главный цикл бота"""
    print("--- ЗАПУСК БОТА CRAFT CARDS (Playwright Async) ---")

    # Инициализировать ViewerTracker
    from chatbot.services.viewer_tracker import ViewerTracker
    from chatbot.services.vk_api_client import VKLiveAPIClient
    from chatbot.constants.cnst_VK import VK_LIVE_API_TOKEN, VK_LIVE_CHANNEL_NAME
    
    vk_api = VKLiveAPIClient(VK_LIVE_API_TOKEN, VK_LIVE_CHANNEL_NAME)
    tracker = ViewerTracker(vk_api)
    
    # Запустить фоновую задачу опроса зрителей
    asyncio.create_task(viewer_poll_task(tracker))
    print("[ViewerPoll] Viewer polling task started")

    pids = set()
    user_last_action = {}

    async with async_playwright() as p:
        browser = None
        while True:
            try:
                if browser is None:
                    await asyncio.sleep(2)  # Задержка перед стартом
                    print("[BOT] Запуск браузера...")

                    # Использовать существующий профиль если есть
                    user_data_dir = str(CHROME_PROFILE_PATH)
                    print(f"[BOT] Using profile: {user_data_dir}")

                    browser = await p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=False,
                        slow_mo=100,
                        args=[
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-gpu",
                            "--disable-software-rasterizer"
                        ]
                    )

                    # Проверить наличие страниц
                    page = browser.pages[0] if browser.pages else await browser.new_page()

                    print(f"[BOT] Переход на страницу: {CHAT_PAGE_URL}")
                    await page.goto(CHAT_PAGE_URL, wait_until="networkidle", timeout=60000)

                    # Проверить авторизацию
                    if "login" in page.url or not await page.query_selector("//div[contains(@class, 'ChatMessage_root')]"):
                        print("[BOT] !!! ТРЕБУЕТСЯ АВТОРИЗАЦИЯ !!! У вас есть 60 секунд, чтобы войти в VK.")
                        await asyncio.sleep(60)

                    await asyncio.sleep(BOT_PAGE_LOAD_WAIT)
                    print("[BOT] Бот готов и слушает чат...")

                # Извлечь сообщения
                msg_elements = await page.query_selector_all("//div[contains(@class, 'ChatMessage_root')]")

                # Обрабатывать только последние 20 сообщений
                for el in msg_elements[-20:]:
                    try:
                        mid = await el.get_attribute("data-message-id")
                        if not mid or mid in pids:
                            continue

                        # Извлечь текст
                        text_el = await el.query_selector('span[data-role="markup"]')
                        if not text_el:
                            continue
                        text = (await text_el.inner_text()).strip()

                        # Извлечь отправителя
                        sender_el = await el.query_selector('span[class*="ChatMessageAuthorPanel_name"]')
                        if not sender_el:
                            continue
                        sender_name = (await sender_el.inner_text()).strip().replace(':', '')

                        # Извлечь получателя (для личных сообщений)
                        recipient = None
                        mention_el = await el.query_selector(".mention")
                        if mention_el:
                            recipient = await mention_el.get_attribute("data-display-name")

                        pids.add(mid)
                        if len(pids) > BOT_CACHE_LIMIT:
                            pids = set(list(pids)[-BOT_CACHE_CLEANUP:])

                        # Пропустить команды боту (/w)
                        if text.lower().startswith("/w "):
                            if sender_name == "CraftCards Bot":
                                await delete_message_via_api(mid)
                            continue

                        # Debounce (защита от спама)
                        now = time.time()
                        if sender_name in user_last_action and now - user_last_action[sender_name] < DEBOUNCE_SECONDS:
                            continue
                        user_last_action[sender_name] = now

                        # Передать в обработчик
                        msg_data = {
                            "id": mid,
                            "text": text,
                            "sender": sender_name,
                            "recipient": recipient
                        }

                        await process_message(msg_data)

                    except Exception as e:
                        print(f"[BOT] Msg Proc Error: {e}")

                await asyncio.sleep(BOT_POLL_INTERVAL)

            except Exception as e:
                print(f"[BOT] Global Loop Error: {e}. Restarting in {BOT_ERROR_WAIT}s")
                if browser:
                    await browser.close()
                browser = None
                await asyncio.sleep(BOT_ERROR_WAIT)


if __name__ == "__main__":
    asyncio.run(bot_task())
