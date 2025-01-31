# System Sentinel 🖥️🛡️

## Overview
System Sentinel is a comprehensive system diagnostics and monitoring tool that provides real-time insights into system health, performance, and potential issues across multiple platforms.

### Features
* Cross-platform support (Windows, Linux, macOS)
* Real-time system metrics collection
* Hardware health monitoring
* Configurable alert system
* Web dashboard for system insights

## Project Structure
```
system_diagnostics/
🔼
🔽 frontend/                # React frontend directory
│   🔽 src/
│   │   🔽 app/
│   │   🔽 components/
│   │   🔽 lib/
│   🔽 public/
│   🔽 package.json
│
🔽 backend/                 # Flask backend directory
│   🔽 src/
│   │   🔽 core/
│   │   │   🔽 __init__.py
│   │   │   🔽 diagnostics.py
│   │   │   🔽 analyzer.py
│   │   🔽 database/
│   │   │   🔽 __init__.py
│   │   │   🔽 db_handler.py
│   │   🔽 utils/
│   │   │   🔽 __init__.py
│   │   │   🔽 access.py
│   │   │   🔽 base.py
│   │   │   🔽 alerts.py
│   │   🔽 api/             # New directory for API routes
│   │       🔽 __init__.py
│   │       🔽 metrics.py
│   │       🔽 system.py
│   🔽 static/
│   │   🔽 favicon.ico
│   │   🔽 js/
│   │       🔽 dashboard.js
│   🔽 templates/
│   │   🔽 index.html
│   │   🔽 dashboard.html
│   │   🔽 error.html
│   🔽 config.py
│   🔽 requirements.txt
│   🔽 app.py
│
🔽 tests/                   # Separate directory for tests
│   🔽 test_core/
│   🔽 test_api/
│   🔽 test_database/
│
🔽 .env                     # Environment variables
🔽 .gitignore
🔽 README.md
```

## Prerequisites
- Python 3.8+
- Git
- Virtual environment support

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/system-sentinel.git
cd system-sentinel
```

### 2. Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Comprehensive Requirements File
Create a `requirements.txt` with the following contents:

```
# System Monitoring
psutil==5.9.0
GPUtil==1.4.0
wmi==1.5.1
pywin32==306

# Web Framework
flask==2.0.1
requests==2.26.0

# Database
sqlalchemy==1.4.23

# Configuration and Utilities
python-dotenv==0.19.0
apscheduler==3.8.1
pytz==2023.3

# Optional: Logging and Debugging
logging
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configuration
1. Copy `.env.example` to `.env`
2. Configure environment variables for monitoring thresholds and alert settings

#### `.env` File
Create a `.env` file in the project root:
```
# Database Configuration
DATABASE_URL=sqlite:///system_diagnostics.db

# Monitoring Thresholds
CPU_TEMP_MAX=85
CPU_USAGE_MAX=90
MEMORY_USAGE_MAX=90
DISK_USAGE_MAX=90

# Alert Configuration
EMAIL_ALERTS_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@example.com
SENDER_PASSWORD=your_app_password

# Webhook Alerts
WEBHOOK_ALERTS_ENABLED=false
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
```

### 6. Running the Application
```bash
# Activate virtual environment first
python app.py
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push and create a pull request

### Troubleshooting
- Ensure all dependencies are correctly installed
- Check `.env` file configurations
- Verify Python version compatibility

### Platform-Specific Notes
- Windows: Requires `pywin32` for system monitoring
- Linux/macOS: Some Windows-specific modules may need alternatives

## License
MIT License

