from redmail import gmail
import gmail_secrets
import os
import time

def send_alert(message):
    gmail.username = gmail_secrets.username
    gmail.password = gmail_secrets.password
    gmail.send(
        subject="Wild Orchid Starlink - GPS Alert",
        receivers=['paul.bouchier@gmail.com'],
        text=message
    )

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
