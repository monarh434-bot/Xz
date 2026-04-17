import os
import json
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ВПИШИ СВОИ ДАННЫЕ СЮДА
API_ID = 730880
API_HASH = "9ca11338796d375b98ab716bc20603d7"
SESSION_STRING = "1ApWapzMBu2vS2rtxe3o3dtMRcH8ugH0s-8WGEHL2EsNgKM7LJyFH7jj8KPhBAEWpEKTtS_aV8siRtsfeQEdDeYYx65yFs8v5qsfQcqzUmBp2-ag4h9K1gK6T7YTUlrqiXE-naCCrNDkFHjNnDvQ1D36GylCKBQ6_DI9UmoMxRxs9D6w7IAmHNPQwN7Gh6ZAY-KrhxkgrznRpv10712PrKoOIsSZ7FsUx_ti7YT7lUAeBxNIlLAMEsFP01FZf-Y_skijR-IFU_xHtjsCKr9yMI6k41YAlato8Mw_cZLSGaQ1ZB87XIkR-mrBZGMTe8wqz0Dnw6KYiykaJVEotnUB-5QSbf9RMYg8="

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "source_chat": None,
    "target_bot": None,
    "forward_mode": "file"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = DEFAULT_CONFIG.copy()
        cfg.update(data)
        return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def normalize_session_string(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    for d in ("—", "–", "−"):
        value = value.replace(d, "-")
    if value.lower().startswith("session string ="):
        value = value.split("=", 1)[1].strip()
    value = value.replace("\n", "").replace("\r", "").strip()
    return value

SESSION_STRING = normalize_session_string(SESSION_STRING)
config = load_config()
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/helpme$"))
async def help_cmd(event):
    await event.reply(
        "Команды:\n"
        "/grouplook — сохранить текущую группу\n"
        "/grouplook -1001234567890 — сохранить группу по ID\n"
        "/botlook — сохранить текущий чат как получателя\n"
        "/botlook @username_bot — сохранить получателя вручную\n"
        "/mode file — отправка как файл\n"
        "/mode forward — пересылка форвардом\n"
        "/status — показать настройки"
    )

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/status$"))
async def status_cmd(event):
    await event.reply(
        "Текущие настройки:\n"
        f"source_chat: {config.get('source_chat')}\n"
        f"target_bot: {config.get('target_bot')}\n"
        f"forward_mode: {config.get('forward_mode')}"
    )

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/mode\s+(file|forward)$"))
async def mode_cmd(event):
    mode = event.pattern_match.group(1).lower()
    config["forward_mode"] = mode
    save_config(config)
    await event.reply(f"Режим сохранён: {mode}")

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/grouplook(?:\s+(-?\d+))?$"))
async def grouplook_cmd(event):
    manual_id = event.pattern_match.group(1)
    if manual_id:
        config["source_chat"] = int(manual_id)
        save_config(config)
        await event.reply(f"Группа сохранена вручную: {manual_id}")
        return
    config["source_chat"] = event.chat_id
    save_config(config)
    await event.reply(f"Текущая группа сохранена: {event.chat_id}")

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/botlook(?:\s+(.+))?$"))
async def botlook_cmd(event):
    manual_target = event.pattern_match.group(1)
    if manual_target:
        config["target_bot"] = manual_target.strip()
        save_config(config)
        await event.reply(f"Получатель сохранён вручную: {config['target_bot']}")
        return
    chat = await event.get_chat()
    username = getattr(chat, "username", None)
    if username:
        config["target_bot"] = f"@{username}"
    else:
        config["target_bot"] = event.chat_id
    save_config(config)
    await event.reply(f"Текущий чат сохранён как получатель: {config['target_bot']}")

@client.on(events.NewMessage)
async def photo_forwarder(event):
    try:
        if config.get("source_chat") is None or config.get("target_bot") is None:
            return
        if event.chat_id != config["source_chat"]:
            return
        if not event.photo:
            return

        target = config["target_bot"]
        mode = config.get("forward_mode", "file")

        if mode == "forward":
            await client.forward_messages(target, event.message)
            print(f"[OK] Фото переслано форвардом: {event.message.id}")
            return

        temp_path = await event.download_media(file="/tmp/")
        if not temp_path:
            print("[WARN] Фото не скачалось")
            return

        try:
            await client.send_file(target, temp_path, caption="Фото из группы")
            print(f"[OK] Фото отправлено файлом: {temp_path}")
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
    except Exception as e:
        print(f"[ERROR] Ошибка обработки фото: {e}")

async def main():
    if not SESSION_STRING or "PASTE_SESSION_STRING_HERE" in SESSION_STRING:
        raise RuntimeError("Вставь SESSION_STRING в main.py")
    if not API_HASH or "PASTE_API_HASH_HERE" in API_HASH:
        raise RuntimeError("Вставь API_HASH в main.py")

    await client.connect()

    if not await client.is_user_authorized():
        raise RuntimeError("SESSION_STRING невалидна или не подходит к API_ID/API_HASH")

    me = await client.get_me()
    print(f"[START] Userbot запущен: id={me.id} username={getattr(me, 'username', None)}")
    print(f"[START] source_chat={config.get('source_chat')}")
    print(f"[START] target_bot={config.get('target_bot')}")
    print(f"[START] forward_mode={config.get('forward_mode')}")

if __name__ == "__main__":
    asyncio.run(main())
    client.run_until_disconnected()
