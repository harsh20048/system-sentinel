from datetime import datetime, timedelta
import wmi
import win32evtlog
import logging
import winreg
from typing import Dict, List, Optional, Any, Union
import traceback
import pythoncom

logger = logging.getLogger(__name__)


class SystemAnalyzer:
    def __init__(self, thresholds: Dict[str, Any] = None):
        self.thresholds = thresholds or {
            'cpu_temp_max': 85,  # °C
            'cpu_usage_max': 90,  # %
            'memory_usage_max': 90,  # %
            'disk_usage_max': 90,  # %
            'gpu_temp_max': 85   # °C   
        }
        if thresholds:
                # Ensure all threshold values are converted to float
            self.thresholds.update({k: float(v) for k, v in thresholds.items()})

        try:
            logger.debug("Attempting WMI initialization")
            self.computer = self._initialize_wmi()
            logger.info("WMI initialized successfully")
        except Exception as e:
            logger.error(f"WMI Initialization Failed: {e}")
            logger.error(f"Detailed Traceback: {traceback.format_exc()}")
            self.computer = None

    def _initialize_wmi(self):
        """
        Robust WMI initialization with alternative connection strategies
        """
        try:
            # Initialize COM libraries
            pythoncom.CoInitialize()

            # Try different connection strategies
            connection_attempts = [
                lambda: wmi.WMI(),  # Default connection
                lambda: wmi.WMI(privileges=["SecurityPrivilege"]),
                lambda: wmi.WMI(computer=".", privileges=["SecurityPrivilege"])
            ]

            for attempt in connection_attempts:
                try:
                    computer = attempt()
                    return computer
                except Exception as e:
                    logger.warning(f"WMI connection attempt failed: {e}")

            logger.error("All WMI connection attempts failed")
            return None

        except Exception as e:
            logger.error(f"Critical WMI initialization error: {e}")
            return None
        finally:
            # Ensure COM is properly uninitialized
            pythoncom.CoUninitialize()
        
            
    def _safe_float_conversion(self, value: Any) -> Optional[float]:
        """Safely convert a value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert value '{value}' to float")
            return None

    def analyze_hardware_health(self, diagnostics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze hardware health based on diagnostics data

        Args:
            diagnostics_data (dict): Dictionary containing system diagnostics data

        Returns:
            dict: Analysis results including status, warnings, and component details
        """
        if not diagnostics_data or not isinstance(diagnostics_data, dict):
            return {
                'status': 'error',
                'warnings': ['Invalid diagnostics data'],
                'components': {}
            }

        analysis = {
            'status': 'healthy',
            'warnings': [],
            'components': {}
        }

        # Analyze CPU
        if 'cpu' in diagnostics_data:
            cpu_health = self._analyze_cpu(diagnostics_data['cpu'])
            analysis['components']['cpu'] = cpu_health
            if cpu_health['warnings']:
                analysis['warnings'].extend(cpu_health['warnings'])

        # Analyze Memory
        if 'memory' in diagnostics_data:
            memory_health = self._analyze_memory(diagnostics_data['memory'])
            analysis['components']['memory'] = memory_health
            if memory_health['warnings']:
                analysis['warnings'].extend(memory_health['warnings'])

        # Analyze Storage
        if 'disk' in diagnostics_data:
            storage_health = self._analyze_storage(diagnostics_data['disk'])
            analysis['components']['storage'] = storage_health
            if storage_health['warnings']:
                analysis['warnings'].extend(storage_health['warnings'])

        # Analyze GPU
        if 'gpu' in diagnostics_data:
            gpu_health = self._analyze_gpu(diagnostics_data['gpu'])
            analysis['components']['gpu'] = gpu_health
            if gpu_health['warnings']:
                analysis['warnings'].extend(gpu_health['warnings'])

        # Update overall status
        if analysis['warnings']:
            analysis['status'] = 'warning'

        return analysis

    def _analyze_cpu(self, cpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CPU health"""
        warnings = []
        status = 'healthy'

        if not cpu_data or not isinstance(cpu_data, dict):
            return {
                'status': 'error',
                'warnings': ['CPU data unavailable'],
                'metrics': {
                    'usage': None,
                    'temperature': None
                }
            }

        current_usage = cpu_data.get('current_usage')
        if current_usage is not None:
            try:
                current_usage = float(current_usage)  # Convert to float
                if current_usage > float(self.thresholds['cpu_usage_max']):
                    warnings.append(f"CPU usage is critically high: {current_usage}%")
                    status = 'warning'
            except (ValueError, TypeError):
                warnings.append("Invalid CPU usage value")
                current_usage = None

        temperature = cpu_data.get('temperature')
        if temperature is not None:
            try:
                temperature = float(temperature)  # Convert to float
                if temperature > float(self.thresholds['cpu_temp_max']):
                    warnings.append(f"CPU temperature is critically high: {temperature}°C")
                    status = 'warning'
            except (ValueError, TypeError):
                warnings.append("Invalid temperature value")
                temperature = None

        return {
            'status': status,
            'warnings': warnings,
            'metrics': {
                'usage': current_usage,
                'temperature': temperature
            }
        }

    def _analyze_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze memory health"""
        warnings = []
        status = 'healthy'

        if not memory_data or not isinstance(memory_data, dict):
            return {
                'status': 'error',
                'warnings': ['Memory data unavailable'],
                'metrics': {
                    'usage_percent': None,
                    'swap_percent': None
                }
            }

        percent_used = memory_data.get('percent_used')
        if percent_used is not None:
            try:
                percent_used = float(percent_used)  # Convert to float
                if percent_used > float(self.thresholds['memory_usage_max']):
                    warnings.append(f"Memory usage is critically high: {percent_used}%")
                    status = 'warning'
            except (ValueError, TypeError):
                warnings.append("Invalid memory usage value")
                percent_used = None

        swap_data = memory_data.get('swap_memory', {})
        swap_percent = swap_data.get('percent')
        if swap_percent is not None:
            try:
                swap_percent = float(swap_percent)  # Convert to float
                if swap_percent > self.thresholds['memory_usage_max']:
                    warnings.append(f"Swap usage is critically high: {swap_percent}%")
                    status = 'warning'
            except (ValueError, TypeError):
                warnings.append("Invalid swap usage value")
                swap_percent = None
        return {
            'status': status,
            'warnings': warnings,
            'metrics': {
                'usage_percent': percent_used,
                'swap_percent': swap_percent
            }
        }

    def _analyze_storage(self, disk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze storage health"""
        warnings = []
        status = 'healthy'
        metrics = {}

        if not disk_data or not isinstance(disk_data, dict):
            return {
                'status': 'error',
                'warnings': ['Storage data unavailable'],
                'metrics': {}
            }

        for device, data in disk_data.items():
            if not isinstance(data, dict):
                continue

            percent_used = data.get('percent_used')
            if percent_used is not None:
                metrics[device] = percent_used
                if percent_used > self.thresholds['disk_usage_max']:
                    warnings.append(f"Disk usage on {device} is critically high: {percent_used}%")
                    status = 'warning'

        return {
            'status': status,
            'warnings': warnings,
            'metrics': metrics
        }

    def _analyze_gpu(self, gpu_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze GPU health"""
        warnings = []
        status = 'healthy'
        metrics = {}

        if not gpu_data or not isinstance(gpu_data, list):
            return {
                'status': 'error',
                'warnings': ['GPU data unavailable'],
                'metrics': {}
            }

        for idx, gpu in enumerate(gpu_data):
            if not isinstance(gpu, dict):
                continue

            gpu_name = gpu.get('name', f'GPU {idx}')
            temperature = gpu.get('temperature')
            load = gpu.get('load')

            if temperature is not None:
                metrics[f"{gpu_name}_temp"] = temperature
                if temperature > self.thresholds['gpu_temp_max']:
                    warnings.append(f"GPU temperature is critically high on {gpu_name}: {temperature}°C")
                    status = 'warning'

            if load is not None:
                metrics[f"{gpu_name}_load"] = load
                # Using CPU threshold for GPU load
                if load > self.thresholds['cpu_usage_max']:
                    warnings.append(f"GPU load is critically high on {gpu_name}: {load}%")
                    status = 'warning'

        return {
            'status': status,
            'warnings': warnings,
            'metrics': metrics
        }

    def check_recent_changes(self, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check for recent hardware and software changes

        Args:
            days (int): Number of days to look back for changes

        Returns:
            dict: Dictionary containing hardware and software changes
        """
        changes = {
            'hardware': self._check_hardware_changes(days),
            'software': self._check_software_changes(days)
        }
        return changes

    def _check_hardware_changes(self, days: int) -> List[Dict[str, Any]]:
        """Check Windows Event Log for hardware changes"""
        changes = []
        try:
            hand = win32evtlog.OpenEventLog(None, "System")
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

            while True:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    break

                for event in events:
                    if event.TimeGenerated < datetime.now() - timedelta(days=days):
                        break

                    # Hardware-related event IDs
                    if event.EventID in [10000, 10001, 10002, 10100]:
                        change_info = {
                            'timestamp': event.TimeGenerated.isoformat(),
                            'event_id': event.EventID,
                            'description': str(event.StringInserts) if event.StringInserts else 'No description available'
                        }

                        # Add source information if available
                        if hasattr(event, 'SourceName'):
                            change_info['source'] = event.SourceName

                        changes.append(change_info)

            win32evtlog.CloseEventLog(hand)
        except Exception as e:
            logger.error(f"Error checking hardware changes: {e}")

        return changes

    def _check_software_changes(self, days: int) -> List[Dict[str, Any]]:
        """Check for software installation and updates with enhanced error handling"""
        changes = []

        # Try WMI method first
        wmi_success = False
        if self.computer:
            try:
                query = """
                    SELECT Name, Version, Vendor, InstallDate 
                    FROM Win32_Product 
                    WHERE InstallDate IS NOT NULL
                """
                current_date = datetime.now()

                for product in self.computer.query(query):
                    try:
                        if product.InstallDate:
                            try:
                                # Ensure install date is properly formatted
                                if len(product.InstallDate) == 8:  # YYYYMMDD format
                                    install_date = datetime.strptime(
                                        product.InstallDate, '%Y%m%d')
                                    if (current_date - install_date).days <= days:
                                        changes.append({
                                            'type': 'installation',
                                            'name': str(product.Name) if product.Name else 'Unknown',
                                            'version': str(product.Version) if product.Version else 'Unknown',
                                            'vendor': str(product.Vendor) if product.Vendor else 'Unknown',
                                            'install_date': product.InstallDate
                                        })
                            except ValueError as date_err:
                                logger.warning(f"Error parsing install date for {
                                               product.Name}: {date_err}")
                                continue
                    except Exception as product_err:
                        logger.warning(
                            f"Error processing product info: {product_err}")
                        continue
                wmi_success = True
            except Exception as wmi_err:
                logger.error(f"Error checking software changes via WMI: {
                             str(wmi_err)}")

        # If WMI method failed or didn't find any changes, try registry method
        if not wmi_success or not changes:
            try:
                keys_to_check = [
                    (winreg.HKEY_LOCAL_MACHINE,
                     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_LOCAL_MACHINE,
                     r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
                ]

                for root_key, subkey_path in keys_to_check:
                    try:
                        with winreg.OpenKey(root_key, subkey_path) as key:
                            for i in range(winreg.QueryInfoKey(key)[0]):
                                try:
                                    subkey_name = winreg.EnumKey(key, i)
                                    with winreg.OpenKey(key, subkey_name) as subkey:
                                        try:
                                            # Get install date if available
                                            try:
                                                install_date = winreg.QueryValueEx(
                                                    subkey, "InstallDate")[0]
                                            except WindowsError:
                                                continue

                                            name = winreg.QueryValueEx(
                                                subkey, "DisplayName")[0]
                                            version = winreg.QueryValueEx(
                                                subkey, "DisplayVersion")[0]

                                            # Parse and validate install date
                                            try:
                                                if len(install_date) == 8:  # YYYYMMDD format
                                                    install_datetime = datetime.strptime(
                                                        install_date, '%Y%m%d')
                                                    if (datetime.now() - install_datetime).days <= days:
                                                        changes.append({
                                                            'type': 'installation',
                                                            'name': str(name),
                                                            'version': str(version),
                                                            'vendor': 'Unknown',
                                                            'install_date': install_date
                                                        })
                                            except (ValueError, TypeError):
                                                continue

                                        except WindowsError:
                                            continue
                                except WindowsError:
                                    continue
                    except WindowsError as key_err:
                        logger.warning(f"Error accessing registry key {
                                       subkey_path}: {str(key_err)}")
                        continue

            except Exception as reg_err:
                logger.error(f"Error checking registry for software changes: {
                             str(reg_err)}")

        return changes

    def health_check(self):
        """Default health check method"""
        return self.computer is not None
