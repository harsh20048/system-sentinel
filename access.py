import os
import sys
import platform
import ctypes
import logging
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def request_admin_privileges():
    """Attempt to elevate privileges on Windows."""
    if platform.system().lower() != 'windows':
        messagebox.showinfo(
            "Elevation Not Supported",
            "Automatic privilege elevation is only supported on Windows. "
            "Please run the application with sudo/root privileges."
        )
        return False

    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True

        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    except Exception as e:
        messagebox.showerror(
            "Elevation Failed",
            f"Could not obtain administrative access: {str(e)}"
        )
        return False

if not request_admin_privileges():
    print("Unable to run the project without administrative privileges.")
    sys.exit(1)


class PermissionError(Exception):
    """Custom exception for permission-related errors"""
    pass

class AdminAccessRequestDialog:
    def __init__(self, title="Administrative Access Required"):
        """
        Create a dialog to request administrative access
        """
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        self.access_granted = False

    def show_access_request(self, message: str = None) -> bool:
        """
        Show a dialog requesting administrative access
        
        Args:
            message (str, optional): Custom message to display
        
        Returns:
            bool: True if user grants access, False otherwise
        """
        default_message = (
            "This application requires administrative privileges to collect comprehensive system diagnostics.\n\n"
            "Would you like to restart the application with administrative rights?"
        )
        
        full_message = message or default_message
        
        # Use messagebox to prompt for elevation
        result = messagebox.askyesno(
            "Administrative Access Required", 
            full_message, 
            icon=messagebox.QUESTION
        )
        
        return result

    def attempt_elevation(self) -> bool:
        """
        Attempt to elevate privileges on Windows
        
        Returns:
            bool: True if elevation is successful, False otherwise
        """
        if platform.system().lower() != 'windows':
            # For non-Windows systems, show a different message
            messagebox.showinfo(
                "Elevation Not Supported", 
                "Automatic privilege elevation is only supported on Windows. "
                "Please run the application with sudo/root privileges."
            )
            return False
        
        try:
            # Check if already running as admin
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            
            # Restart the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1
            )
            
            # Exit the current process
            sys.exit(0)
        
        except Exception as e:
            logger.error(f"Failed to elevate privileges: {str(e)}")
            messagebox.showerror(
                "Elevation Failed", 
                f"Could not obtain administrative access: {str(e)}"
            )
            return False

class SystemAccessHandler:
    def __init__(self, require_admin: bool = False):
        """
        Initialize the SystemAccessHandler
        
        Args:
            require_admin (bool): If True, raises PermissionError when not running with admin privileges
        """
        self.is_windows = platform.system().lower() == 'windows'
        self.is_linux = platform.system().lower() == 'linux'
        self.is_mac = platform.system().lower() == 'darwin'
        
        self.platform_info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
        
        self.start_time = datetime.now()
        self.is_admin = self._check_admin()
        
        if require_admin and not self.is_admin:
            self._handle_admin_access()

    def _handle_admin_access(self):
        """
        Handle scenarios where administrative access is required
        """
        dialog = AdminAccessRequestDialog()
        
        if dialog.show_access_request():
            # Attempt to elevate privileges
            dialog.attempt_elevation()
        else:
            # If user declines, raise a custom exception
            raise PermissionError(
                "Administrative access is required to run this application. "
                "Please restart with appropriate privileges."
            )

    def _check_admin(self) -> bool:
        """
        Check if the current process has administrative privileges
        
        Returns:
            bool: True if running with admin/root privileges, False otherwise
        """
        try:
            if self.is_windows:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception as e:
            logger.error(f"Error checking admin privileges: {str(e)}")
            return False

    def _get_windows_features(self) -> Dict[str, bool]:
        """Get features specific to Windows platform"""
        return {
            'wmi_monitoring': True,
            'windows_performance_counters': True,
            'system_restore': self.is_admin,
            'advanced_windows_logging': self.is_admin
        }

    def _get_linux_features(self) -> Dict[str, bool]:
        """Get features specific to Linux platform"""
        return {
            'systemd_monitoring': True,
            'kernel_log_access': self.is_admin,
            'system_performance_tools': True
        }

    def _get_mac_features(self) -> Dict[str, bool]:
        """Get features specific to macOS platform"""
        return {
            'system_log_access': self.is_admin,
            'time_machine_backup': self.is_admin,
            'performance_monitoring': True
        }

    def get_available_features(self) -> Dict[str, bool]:
        """
        Determine which system monitoring features are available based on
        platform and privileges
        
        Returns:
            Dict[str, bool]: Dictionary of feature names and their availability
        """
        features = {
            # Basic metrics (usually available to all users)
            'cpu_metrics': True,
            'memory_metrics': True,
            'disk_metrics': True,
            'network_metrics': True,
            
            # Advanced features (may require elevated privileges)
            'gpu_metrics': self.is_admin,
            'process_control': self.is_admin,
            'service_control': self.is_admin,
            'hardware_sensors': self.is_admin,
            'system_logs': self.is_admin,
            'power_management': self.is_admin,
            'security_scanning': self.is_admin,
            'backup_restore': self.is_admin,
            'remote_management': False
        }
        
        # Platform-specific feature updates
        if self.is_windows:
            features.update(self._get_windows_features())
        elif self.is_linux:
            features.update(self._get_linux_features())
        elif self.is_mac:
            features.update(self._get_mac_features())
            
        return features

def initialize_system_access(require_admin: bool = False) -> Tuple[SystemAccessHandler, Dict[str, bool]]:
    """
    Initialize the system access handler and return both the handler
    and the available features dictionary
    
    Args:
        require_admin (bool): If True, raises PermissionError when not running with admin privileges
        
    Returns:
        Tuple[SystemAccessHandler, Dict[str, bool]]: Handler instance and available features
        
    Raises:
        PermissionError: If require_admin is True and process lacks admin privileges
    """
    try:
        # Create access handler with admin requirement
        access_handler = SystemAccessHandler(require_admin=require_admin)
        
        # Get available features
        available_features = access_handler.get_available_features()
        
        logger.info("System access initialized successfully")
        return access_handler, available_features
        
    except Exception as e:
        if require_admin:
            # If admin is required and access fails, show elevation dialog
            dialog = AdminAccessRequestDialog()
            
            if dialog.show_access_request():
                # Attempt to elevate privileges
                dialog.attempt_elevation()
            
        logger.error(f"Failed to initialize system access: {str(e)}")
        raise

if __name__ == '__main__':
    # Example usage
    try:
        handler, features = initialize_system_access()
        print("\nSystem Information:")
        for key, value in handler.platform_info.items():
            print(f"{key}: {value}")
            
        print("\nAvailable Features:")
        for feature, available in features.items():
            print(f"{feature}: {'✓' if available else '✗'}")
            
    except Exception as e:
        print(f"Error: {str(e)}")