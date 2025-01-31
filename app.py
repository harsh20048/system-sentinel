import sys
import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from src.core.diagnostics import SystemDiagnostics
from src.core.analyzer import SystemAnalyzer
from src.database.db_handler import DatabaseHandler
from src.core.access import initialize_system_access
from datetime import datetime
import logging
import traceback
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import webbrowser
import threading
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def load_configuration(force_admin: bool = False):
    """Load configuration with optional administrative access"""
    try:
        # Try to initialize system access with admin requirement based on force_admin
        access_handler, available_features = initialize_system_access(
            require_admin=force_admin)

        config = {
            'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///system_diagnostics.db'),
            'AVAILABLE_FEATURES': available_features,
            'THRESHOLDS': {
                'cpu_temp_max': int(os.getenv('CPU_TEMP_MAX', 85)),
                'cpu_usage_max': int(os.getenv('CPU_USAGE_MAX', 90)),
                'memory_usage_max': int(os.getenv('MEMORY_USAGE_MAX', 90)),
                'disk_usage_max': int(os.getenv('DISK_USAGE_MAX', 90)),
                'gpu_temp_max': int(os.getenv('GPU_TEMP_MAX', 85))
            }
        }
        return config, access_handler
    except Exception as e:
        logger.error(f"Configuration loading failed: {e}")
        raise


def create_app():
    """Factory function to create Flask app with enhanced error handling"""
    app = Flask(__name__,
                static_folder='static',
                static_url_path='/static')

    try:
        # Initial configuration without forcing admin
        config, access_handler = load_configuration(force_admin=False)
        app.config.update(config)
        app.secret_key = os.urandom(24)
    except Exception as initialization_error:
        logger.error(f"Initialization Error: {traceback.format_exc()}")
        sys.last_error = str(initialization_error)

        # Minimal app that shows error with admin access option
        @app.route('/')
        def index():
            return render_template('error.html',
                                   error_message=str(initialization_error),
                                   show_admin_option=True)

        @app.route('/retry_with_admin')
        def retry_with_admin():
            try:
                # Attempt to load configuration with admin privileges
                config, _ = load_configuration(force_admin=True)
                return redirect(url_for('index'))
            except Exception as admin_error:
                return render_template('error.html',
                                       error_message=str(admin_error),
                                       show_admin_option=True)

        return app

    class SystemMonitor:
        def __init__(self, available_features):
            self.components = {}
            self.last_health_check = None
            self.initialization_error = None

            try:
                self.initialize_components(available_features)
            except Exception as e:
                self.initialization_error = e
                logger.error(f"Component initialization failed: {e}")

        def initialize_components(self, available_features):
            try:
                def default_health_check():
                    return True

                diagnostics = SystemDiagnostics(
                    available_features=available_features)
                diagnostics.health_check = default_health_check
                self.components['diagnostics'] = diagnostics

                analyzer = SystemAnalyzer(
                    thresholds=app.config.get('THRESHOLDS', {}))
                analyzer.health_check = default_health_check
                self.components['analyzer'] = analyzer

                database = DatabaseHandler(db_url=app.config['DATABASE_URL'])
                database.health_check = default_health_check
                self.components['database'] = database

                self.check_system_health()
            except Exception as e:
                logger.error(f"Failed to initialize components: {e}")
                raise

        def check_system_health(self):
            health_status = {}
            for name, component in self.components.items():
                try:
                    health_status[name] = component.health_check()
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    health_status[name] = False

            self.last_health_check = datetime.now()
            return health_status

        def get_current_data(self):
            if self.initialization_error:
                raise RuntimeError(f"System initialization failed: {self.initialization_error}")

            try:
                diag_data = self.components['diagnostics'].get_all_diagnostics()
                analysis = self.components['analyzer'].analyze_hardware_health(diag_data)
                return {
                    'diagnostics': diag_data,
                    'analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting current data: {e}")
                raise

    # Create monitor
    monitor = SystemMonitor(config.get('AVAILABLE_FEATURES', {}))

    @app.route('/')
    def index():
        try:
            current_data = monitor.get_current_data()
            # Convert numeric values to float where needed
            if 'analysis' in current_data:
                current_data['analysis'] = {
                    k: float(v) if isinstance(v, (int, float, str)) and str(v).replace('.', '').isdigit() else v
                    for k, v in current_data['analysis'].items()
                }
            return render_template('index.html', system_data=current_data)
        except Exception as e:
            logger.error(f"Error in index route: {str(e)}")
            return render_template('error.html',
                                   error_message=str(e),
                                   show_admin_option=True)

    @app.route('/dashboard')
    def dashboard():
        try:
            current_data = monitor.get_current_data()
            return render_template('dashboard.html', system_data=current_data)
        except Exception as e:
            return render_template('error.html',
                                   error_message=str(e),
                                   show_admin_option=True)

    @app.route('/retry_with_admin')
    def retry_with_admin():
        try:
            config, _ = load_configuration(force_admin=True)
            app.config.update(config)
            return redirect(url_for('dashboard'))
        except Exception as admin_error:
            logger.error(f"Admin elevation failed: {admin_error}")
            return render_template('error.html',
                                   error_message=str(admin_error),
                                   show_admin_option=True)

    @app.route('/api/current')
    def get_current_data():
        try:
            data = monitor.get_current_data()
            return jsonify(data)
        except Exception as e:
            return jsonify({
                'error': 'Failed to collect system data',
                'details': str(e),
                'suggest_admin': True
            }), 500

    @app.route('/api/metrics')
    def get_metrics():
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            data = monitor.get_current_data()
            
            if not data.get('diagnostics', {}).get('basic_metrics'):
                raise ValueError("Missing basic metrics data")
            
            metrics = {
                'cpu': {
                    'timestamps': [current_time],
                    'values': [data['diagnostics']['basic_metrics']['cpu']['percent']]
                },
                'memory': {
                    'timestamps': [current_time],
                    'values': [data['diagnostics']['basic_metrics']['memory']['virtual']['percent']]
                },
                'disk': {
                    'timestamps': [current_time],
                    'values': [next(iter(data['diagnostics'].get('disk', {}).values()), {}).get('percent_used', 0)]
                }
            }
            
            return jsonify(metrics)
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return jsonify({
                'error': str(e),
                'status': 'error'
            }), 500

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/x-icon'
        )

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {str(e)}")
        return render_template('error.html',
                               error_message=str(e),
                               show_admin_option=True), 500

    return app

def check_environment():
    """Check if all required environment variables and directories exist"""
    required_dirs = ['static', 'templates', 'src']
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)
    
    if not os.path.exists('.env'):
        print("Warning: .env file not found. Using default configuration.")

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000/dashboard')

# Application entry point
if __name__ == '__main__':
    try:
        # Check environment
        check_environment()
        
        # Create Flask app
        app = create_app()
        
        # Start browser in a separate thread
        if not os.environ.get('DEBUG'):
            threading.Thread(target=open_browser).start()
        
        # Run the application
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=os.environ.get('DEBUG', 'False').lower() == 'true'
        )
        
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
