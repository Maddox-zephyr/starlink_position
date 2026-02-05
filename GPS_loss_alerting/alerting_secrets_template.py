# Gmail credentials and alerting configuration
gmail_alert_enabled = True
username = 'your.email.alerts@gmail.com'
password = 'your_app_password'

subject="Your Boatname - GPS Alert"
receivers=['your_email1@gmail.com', 'your_email2@yahoo.com']

# Telegram bots credentials
telegram_alert_enabled = True
bots_credentials = [
    {
        # bot1
        "BOT_TOKEN": "BOT1_TOKEN",
        "CHAT_ID": 123456789
    },
    {
        # bot2
        "BOT_TOKEN": "BOT2_TOKEN",
        "CHAT_ID": 987654321
    }
]
