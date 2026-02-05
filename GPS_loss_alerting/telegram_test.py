import requests
import alerting_secrets

message_text = "This is a test message from telegram_test!"

def send_telegram_message(bot_token, chat_id, text):
    """Sends a message to a specified Telegram chat."""
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        response = requests.post(api_url, json={'chat_id': chat_id, 'text': text})
        response.raise_for_status()  # Raise an exception for bad status codes
        print("Message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Example usage: send to all configured bots
for bot in alerting_secrets.bots_credentials:
    token = bot.get("BOT_TOKEN")
    chat = bot.get("CHAT_ID")
    if token and chat:
        send_telegram_message(token, chat, message_text)
    else:
        print("Skipping bot with incomplete credentials:", bot)