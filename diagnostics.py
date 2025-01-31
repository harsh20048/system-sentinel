import os
import platform
import logging
import json
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiagnosticsError(Exception):
    pass

class SystemDiagnostics:
    def __init__(self, available_features: Dict[str, bool] = None):
        self.available_features = available_features or {}
        self.lock = threading.Lock()
        self.last_update = None
        self.cache_duration = 5
        self._cached_data = {}
        self.system = platform.system().lower()
        self.is_windows = self.system == 'windows'
        self.is_linux = self.system == 'linux'
        self.is_mac = self.system == 'darwin'
        
        logger.info(f"Initialized SystemDiagnostics for {platform.system()}")

    def get_all_diagnostics(self) -> Dict[str, Any]:
        with self.lock:
            current_time = datetime.now()
            
            if (self.last_update and 
                (current_time - self.last_update).total_seconds() < self.cache_duration):
                return self._cached_data

            try:
                diagnostics = {
                    'timestamp': current_time.isoformat(),
                    'system_info': self.get_system_info(),
                    'basic_metrics': self.get_basic_metrics()
                }

                if self.available_features.get('hardware_sensors'):
                    diagnostics['sensors'] = self.get_hardware_sensors()

                if self.available_features.get('disk_metrics'):
                    diagnostics['disk'] = self.get_disk_metrics()

                if self.available_features.get('network_metrics'):
                    diagnostics['network'] = self.get_network_metrics()

                self._cached_data = diagnostics
                self.last_update = current_time

                return diagnostics

            except Exception as e:
                logger.error(f"Error collecting diagnostics: {str(e)}")
                raise DiagnosticsError(f"Failed to collect system diagnostics: {str(e)}")

    def get_system_info(self) -> Dict[str, Any]:
        try:
            return {
                'platform': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'boot_time': self._get_boot_time()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {'error': str(e)}

    def _get_boot_time(self) -> str:
        """Get system boot time using platform-specific methods"""
        try:
            if self.is_windows:
                output = subprocess.check_output('systeminfo', shell=True).decode()
                for line in output.split('\n'):
                    if 'System Boot Time:' in line:
                        return line.split(':', 1)[1].strip()
            elif self.is_linux:
                output = subprocess.check_output('uptime -s', shell=True).decode().strip()
                return output
            elif self.is_mac:
                output = subprocess.check_output('sysctl -n kern.boottime', shell=True).decode().strip()
                return output
            return str(datetime.now())
        except Exception as e:
            logger.warning(f"Could not get boot time: {e}")
            return str(datetime.now())

    def get_basic_metrics(self) -> Dict[str, Any]:
        try:
            metrics = {
                'cpu': self._get_cpu_metrics(),
                'memory': self._get_memory_metrics()
            }
            return metrics
        except Exception as e:
            logger.error(f"Error getting basic metrics: {str(e)}")
            return {'error': str(e)}

    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU metrics using system commands"""
        try:
            if self.is_windows:
                output = subprocess.check_output('wmic cpu get loadpercentage', shell=True).decode()
                cpu_load = [int(line.strip()) for line in output.split('\n') if line.strip() and line.strip().isdigit()]
                return {
                    'percent': cpu_load[0] if cpu_load else None,
                    'count': {
                        'physical': len(cpu_load),
                        'logical': len(cpu_load)
                    }
                }
            elif self.is_linux:
                output = subprocess.check_output('top -bn1 | grep "Cpu(s)"', shell=True).decode()
                # Parse Linux top output for CPU usage
                cpu_parts = output.split(',')
                for part in cpu_parts:
                    if '%us' in part:
                        return {
                            'percent': float(part.split('%')[0].strip()),
                            'count': {
                                'physical': len(subprocess.check_output('nproc', shell=True).decode().strip()),
                                'logical': len(subprocess.check_output('nproc', shell=True).decode().strip())
                            }
                        }
            elif self.is_mac:
                output = subprocess.check_output('top -l 1 | grep CPU', shell=True).decode()
                # Parse macOS top output
                return {
                    'percent': float(output.split(',')[0].split(':')[1].strip().rstrip('%')),
                    'count': {
                        'physical': len(subprocess.check_output('sysctl -n hw.physicalcpu', shell=True).decode().strip()),
                        'logical': len(subprocess.check_output('sysctl -n hw.logicalcpu', shell=True).decode().strip())
                    }
                }
            return {'error': 'Unsupported platform'}
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {str(e)}")
            return {'error': str(e)}

    def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory metrics using system commands"""
        try:
            if self.is_windows:
                output = subprocess.check_output('systeminfo', shell=True).decode()
                total_mem, avail_mem = None, None
                for line in output.split('\n'):
                    if 'Total Physical Memory:' in line:
                        total_mem = int(line.split(':')[1].strip().split()[0].replace(',', ''))
                    if 'Available Physical Memory:' in line:
                        avail_mem = int(line.split(':')[1].strip().split()[0].replace(',', ''))
                return {
                    'virtual': {
                        'total': total_mem,
                        'available': avail_mem,
                        'percent': round((total_mem - avail_mem) / total_mem * 100, 2) if total_mem and avail_mem else None
                    }
                }
            elif self.is_linux:
                output = subprocess.check_output('free -b', shell=True).decode()
                mem_lines = [line.split() for line in output.split('\n') if 'Mem:' in line][0]
                return {
                    'virtual': {
                        'total': int(mem_lines[1]),
                        'available': int(mem_lines[3]),
                        'percent': round(float(mem_lines[2]) / float(mem_lines[1]) * 100, 2)
                    }
                }
            elif self.is_mac:
                output = subprocess.check_output('vm_stat', shell=True).decode()
                total_bytes = int(subprocess.check_output('sysctl -n hw.memsize', shell=True).decode().strip())
                page_size = 4096  # Most systems use 4096-byte pages
                
                free_pages = 0
                for line in output.split('\n'):
                    if 'free' in line:
                        free_pages = int(line.split(':')[1].strip().rstrip('.'))
                
                free_bytes = free_pages * page_size
                return {
                    'virtual': {
                        'total': total_bytes,
                        'available': free_bytes,
                        'percent': round((total_bytes - free_bytes) / total_bytes * 100, 2)
                    }
                }
            return {'error': 'Unsupported platform'}
        except Exception as e:
            logger.error(f"Error getting memory metrics: {str(e)}")
            return {'error': str(e)}

    def get_hardware_sensors(self) -> Dict[str, Any]:
        """Collect hardware sensor information using system commands"""
        sensors_data = {'temperature': {}, 'battery': None}

        try:
            if self.is_windows:
                # Windows temperature might require specialized tools
                sensors_data['note'] = 'Detailed sensor data requires additional tools'
            elif self.is_linux:
                # Linux temperature via thermal zone
                try:
                    thermal_zones = os.listdir('/sys/class/thermal')
                    for zone in thermal_zones:
                        try:
                            with open(f'/sys/class/thermal/{zone}/temp', 'r') as f:
                                temp = int(f.read().strip()) / 1000  # Convert millidegrees to degrees
                                sensors_data['temperature'][zone] = temp
                        except Exception:
                            continue
                except Exception:
                    pass
            elif self.is_mac:
                # macOS temperature via system profiler
                try:
                    output = subprocess.check_output('system_profiler SPHardwareDataType', shell=True).decode()
                    for line in output.split('\n'):
                        if 'Temperature' in line:
                            temp = line.split(':')[1].strip()
                            sensors_data['temperature']['system'] = float(temp.rstrip('°C'))
                except Exception:
                    pass

            return sensors_data
        except Exception as e:
            logger.error(f"Error getting hardware sensors: {str(e)}")
            return {'error': str(e)}

    def get_disk_metrics(self) -> Dict[str, Any]:
        """Get disk usage metrics using shutil"""
        try:
            disk_metrics = {}
            
            # Use shutil to get disk usage for various partitions/drives
            partitions = ['/']  # Default to root for Unix-like systems
            if self.is_windows:
                # For Windows, get all drive letters
                partitions = [f'{d}:\\' for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' 
                              if os.path.exists(f'{d}:')]
            
            for partition in partitions:
                try:
                    usage = shutil.disk_usage(partition)
                    disk_metrics[partition] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent_used': round(usage.used / usage.total * 100, 2)
                    }
                except Exception as e:
                    logger.warning(f"Could not get disk usage for {partition}: {e}")
            
            return disk_metrics
        except Exception as e:
            logger.error(f"Error getting disk metrics: {str(e)}")
            return {'error': str(e)}

    def get_network_metrics(self) -> Dict[str, Any]:
        """Get basic network information using system commands"""
        try:
            network_info = {}
            
            if self.is_windows:
                output = subprocess.check_output('ipconfig', shell=True).decode()
                network_info['interfaces'] = self._parse_windows_ipconfig(output)
            elif self.is_linux:
                output = subprocess.check_output('ip addr', shell=True).decode()
                network_info['interfaces'] = self._parse_linux_ip_addr(output)
            elif self.is_mac:
                output = subprocess.check_output('ifconfig', shell=True).decode()
                network_info['interfaces'] = self._parse_mac_ifconfig(output)
            
            return network_info
        except Exception as e:
            logger.error(f"Error getting network metrics: {str(e)}")
            return {'error': str(e)}

    def _parse_windows_ipconfig(self, output):
        """Parse Windows ipconfig output"""
        interfaces = {}
        current_adapter = None
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('Windows IP Configuration'):
                continue
            if ':' in line and not line.startswith(' '):
                current_adapter = line.rstrip(':')
                interfaces[current_adapter] = {}
            if current_adapter and 'IPv4 Address' in line:
                interfaces[current_adapter]['ip'] = line.split(':')[1].strip()
        return interfaces

    def _parse_linux_ip_addr(self, output):
        """Parse Linux ip addr output"""
        interfaces = {}
        current_adapter = None
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('<') and ':' in line:
                current_adapter = line.split(':')[1].split('@')[0].strip()
                interfaces[current_adapter] = {}
            if 'inet ' in line:
                interfaces[current_adapter]['ip'] = line.split('inet ')[1].split()[0]
        return interfaces

    def _parse_mac_ifconfig(self, output):
        """Parse macOS ifconfig output"""
        interfaces = {}
        current_adapter = None
        for line in output.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('\t'):
                current_adapter = line.rstrip(':')
                interfaces[current_adapter] = {}
            if 'inet ' in line:
                interfaces[current_adapter]['ip'] = line.split('inet ')[1].split()[0]
        return interfaces

    def reset_cache(self) -> None:
        with self.lock:
            self.last_update = None
            self._cached_data = {}

    def get_cache_info(self) -> Dict[str, Any]:
        return {
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'cache_duration': self.cache_duration,
            'cache_size': len(json.dumps(self._cached_data)) if self._cached_data else 0
        }