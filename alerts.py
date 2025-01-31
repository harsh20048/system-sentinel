import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime
from config import ALERT_CONFIG

class AlertManager:
    def __init__(self):
        self.email_config = ALERT_CONFIG['email']
        self.webhook_config = ALERT_CONFIG['webhook']
        
    def send_alert(self, alert_type, message, details=None):
        """Send alert through configured channels"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{alert_type.upper()}] {timestamp}\n{message}"
        if details:
            formatted_message += f"\n\nDetails:\n{details}"
        
        if self.email_config['enabled']:
            self._send_email_alert(formatted_message)
        
        if self.webhook_config['enabled']:
            self._send_webhook_alert(alert_type, message, details)
    
    def _send_email_alert(self, message):
        """Send alert via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(self.email_config['recipient_emails'])
            msg['Subject'] = 'System Diagnostics Alert'
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {str(e)}")
    
    def _send_webhook_alert(self, alert_type, message, details):
        """Send alert via webhook"""
        try:
            payload = {
                'type': alert_type,
                'message': message,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(self.webhook_config['url'], json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send webhook alert: {str(e)}")