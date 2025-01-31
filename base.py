# core/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime

class MonitoringComponent(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._last_error: Optional[Exception] = None
        self._error_count: int = 0
        self._last_success: Optional[datetime] = None

    @abstractmethod
    def health_check(self) -> bool:
        """Verify component is functioning correctly"""
        pass

    def log_error(self, error: Exception, context: str = ""):
        self._last_error = error
        self._error_count += 1
        self.logger.error(f"{context}: {str(error)}", exc_info=True)

    def log_success(self):
        self._last_error = None
        self._error_count = 0
        self._last_success = datetime.now()

# core/diagnostics.py
class ImprovedSystemDiagnostics(MonitoringComponent):
    def __init__(self, available_features: Dict[str, bool] = None):
        super().__init__()
        self.available_features = available_features or {}
        self._initialize_components()

    def _initialize_components(self):
        """Initialize monitoring components based on available features"""
        if self.available_features.get('hardware_sensors'):
            self._init_hardware_monitoring()
        if self.available_features.get('gpu_metrics'):
            self._init_gpu_monitoring()

    def health_check(self) -> bool:
        try:
            # Verify basic system metrics can be collected
            basic_metrics = self.get_basic_metrics()
            return bool(basic_metrics and not basic_metrics.get('error'))
        except Exception as e:
            self.log_error(e, "Health check failed")
            return False

# core/analyzer.py
class ImprovedSystemAnalyzer(MonitoringComponent):
    def __init__(self, thresholds: Dict[str, float]):
        super().__init__()
        self.thresholds = thresholds
        self._validators = self._initialize_validators()

    def _initialize_validators(self):
        """Initialize data validation rules"""
        return {
            'cpu_temp': lambda x: 0 <= x <= 150,
            'cpu_usage': lambda x: 0 <= x <= 100,
            'memory_usage': lambda x: 0 <= x <= 100,
            'disk_usage': lambda x: 0 <= x <= 100
        }

    def health_check(self) -> bool:
        try:
            # Verify analyzer can process sample data
            sample_data = {'cpu': {'temperature': 50, 'usage': 30}}
            analysis = self.analyze_hardware_health(sample_data)
            return bool(analysis and not analysis.get('error'))
        except Exception as e:
            self.log_error(e, "Health check failed")
            return False

# database/handler.py
class ImprovedDatabaseHandler(MonitoringComponent):
    def __init__(self, db_url: str):
        super().__init__()
        self.db_url = db_url
        self._initialize_db()

    def health_check(self) -> bool:
        try:
            # Verify database connection and basic operations
            with self.Session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            self.log_error(e, "Database health check failed")
            return False

    def _initialize_db(self):
        """Initialize database with retry mechanism"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.engine = create_engine(
                    self.db_url,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                Base.metadata.create_all(self.engine)
                self.Session = sessionmaker(bind=self.engine)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.log_error(e, f"Database initialization attempt {attempt + 1} failed")