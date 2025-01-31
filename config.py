import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Secret Key Configuration
SECRET_KEY = os.getenv('SECRET_KEY')

# Generate a random secret key if not set
if not SECRET_KEY:
    SECRET_KEY = os.urandom(24).hex()  # Generates a random 24-byte key

# Ensure the secret key is not the default
if SECRET_KEY == 'your_default_secret_key':
    raise ValueError("Please set the SECRET_KEY environment variable for production.")

# Validate required environment variables
if not os.getenv('DATABASE_URL'):
    raise ValueError("DATABASE_URL environment variable is not set.")
if not os.getenv('SENDER_EMAIL') or not os.getenv('SENDER_PASSWORD'):
    raise ValueError("SENDER_EMAIL and SENDER_PASSWORD must be provided for email alerts.")

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///system_diagnostics.db')

# Monitoring Configuration
MONITORING_INTERVAL = int(os.getenv('MONITORING_INTERVAL', 300))  # 5 minutes in seconds

# Alert Thresholds
THRESHOLDS = {
    'cpu_temp_max': float(os.getenv('CPU_TEMP_MAX', '85')),
    'cpu_usage_max': float(os.getenv('CPU_USAGE_MAX', '90')),
    'memory_usage_max': float(os.getenv('MEMORY_USAGE_MAX', '90')),
    'disk_usage_max': float(os.getenv('DISK_USAGE_MAX', '90')),
    'gpu_temp_max': float(os.getenv('GPU_TEMP_MAX', '85'))
}

# Alert Configuration
ALERT_CONFIG = {
    'email': {
        'enabled': os.getenv('EMAIL_ALERTS_ENABLED', 'false').lower() == 'true',
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'sender_email': os.getenv('SENDER_EMAIL', ''),
        'sender_password': os.getenv('SENDER_PASSWORD', ''),
        'recipient_emails': os.getenv('RECIPIENT_EMAILS', '').split(',')
    },
    'webhook': {
        'enabled': os.getenv('WEBHOOK_ALERTS_ENABLED', 'false').lower() == 'true',
        'url': os.getenv('WEBHOOK_URL', '')
    }
}