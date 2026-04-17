from telethon.sync import TelegramClient
from telethon.sessions import StringSession

def main():
    print("=== SESSION_STRING generator ===")
    api_id = int(input("API_ID: ").strip())
    api_hash = input("API_HASH: ").strip()

    with TelegramClient(StringSession(), api_id, api_hash) as client:
        print("\nSESSION_STRING:\n")
        print(client.session.save())
        print("\nСкопируй строку целиком в main.py")

if __name__ == "__main__":
    main()
