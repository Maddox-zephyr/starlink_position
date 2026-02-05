from redmail import gmail
import alerting_secrets
import os
import time
import requests

# If you don't want to send to both gmail and telegram, you can modify this function
# to only call one of the two alerting functions.
def send_alert(message):
    if (alerting_secrets.gmail_alert_enabled):
        send_gmail_alert(message)
    if (alerting_secrets.telegram_alert_enabled):
        send_telegram_alert(message)

# Send email alert
def send_gmail_alert(message):
    gmail.username = alerting_secrets.username
    gmail.password = alerting_secrets.password
    receivers = alerting_secrets.receivers
    subject = alerting_secrets.subject

    gmail.send(
        subject=subject,
        receivers=receivers,
        text=message
    )

# Send Telegram alert
def send_telegram_alert(message):
    # send message to all configured bots
    for bot in alerting_secrets.bots_credentials:
        token = bot.get("BOT_TOKEN")
        chat = bot.get("CHAT_ID")
        if token and chat:
            send_telegram_message(token, chat, message)
        else:
            print("Skipping bot with incomplete credentials:", bot)

def send_telegram_message(bot_token, chat_id, message):
    """Sends a message to a specified Telegram chat."""
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        response = requests.post(api_url, json={'chat_id': chat_id, 'text': message})
        response.raise_for_status()  # Raise an exception for bad status codes
        print("Message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Expand environment variables for file paths
alerts_file = os.path.expandvars('$HOME/logs/starlink_gps_alerts.txt')
sent_alerts_log = os.path.expandvars('$HOME/logs/starlink_gps_sent_alerts.txt')

def main():
    print("starting starlink_gps_alert")
    send_alert('Starlink GPS alert: started alerting service')

    try:
        while True:
            # Check if the alerts file exists and has content
            if os.path.exists(alerts_file) and os.path.getsize(alerts_file) > 0:
                # Read the file contents
                with open(alerts_file, 'r') as f:
                    message = f.read()
                
                # Send the alert
                send_alert(message)
                
                # Append the message to the sent alerts log
                with open(sent_alerts_log, 'a') as f:
                    f.write(message + '\n')
                
                # Truncate the alerts file to zero length
                with open(alerts_file, 'w') as f:
                    f.write('')
            
            # Poll once each minute
            time.sleep(60)

    except Exception as e:
        error_message = f'starlink_gps_alert: Exception occurred: {str(e)}'
        send_alert(error_message)
        exit(1)

if __name__ == "__main__":
    main()
