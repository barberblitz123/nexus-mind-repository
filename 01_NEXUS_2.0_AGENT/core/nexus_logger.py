#!/usr/bin/env python3
"""
NEXUS 2.0 Logger System
Comprehensive logging and debugging for all components
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import traceback
from enum import Enum
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for colored output
colorama.init()

class LogLevel(Enum):
    """Log levels with colors"""
    DEBUG = (logging.DEBUG, Fore.CYAN)
    INFO = (logging.INFO, Fore.GREEN)
    WARNING = (logging.WARNING, Fore.YELLOW)
    ERROR = (logging.ERROR, Fore.RED)
    CRITICAL = (logging.CRITICAL, Fore.RED + Back.YELLOW)
    
class NexusLogger:
    """Central logging system for NEXUS 2.0"""
    
    def __init__(self, name: str = "NEXUS", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_file_handler()
        self._setup_console_handler()
        self._setup_debug_handler()
        self._setup_audit_handler()
        
        # Activity tracking
        self.activity_log = []
        self.error_log = []
        self.agent_logs = {}  # Separate logs per agent
        self.audit_log = []  # Audit trail for important events
        
    def _setup_file_handler(self):
        """Setup file logging"""
        # Main log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"nexus_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed format for file
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # Also create a latest.log symlink
        latest_log = self.log_dir / "latest.log"
        if latest_log.exists():
            latest_log.unlink()
        latest_log.symlink_to(log_file.name)
        
    def _setup_audit_handler(self):
        """Setup audit logging"""
        audit_file = self.log_dir / "audit.log"
        
        audit_handler = logging.FileHandler(audit_file, mode='a')
        audit_handler.setLevel(logging.INFO)
        
        # Audit format with timestamp and details
        audit_format = logging.Formatter(
            '%(asctime)s | AUDIT | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(audit_format)
        
        # Create separate audit logger
        self.audit_logger = logging.getLogger(f"{self.name}.audit")
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.addHandler(audit_handler)
        
    def _setup_console_handler(self):
        """Setup console logging with colors"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Custom formatter with colors
        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                # Get color for level
                for level in LogLevel:
                    if record.levelno == level.value[0]:
                        color = level.value[1]
                        break
                else:
                    color = Fore.WHITE
                    
                # Format message
                timestamp = datetime.now().strftime("%H:%M:%S")
                prefix = f"{color}[{timestamp}] {record.levelname:<8}{Style.RESET_ALL}"
                
                # Add module info for debug
                if record.levelno <= logging.DEBUG:
                    prefix += f" {Fore.BLUE}({record.name}){Style.RESET_ALL}"
                    
                return f"{prefix} {record.getMessage()}"
                
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)
        
    def _setup_debug_handler(self):
        """Setup debug file with full details"""
        debug_file = self.log_dir / "debug.log"
        
        debug_handler = logging.FileHandler(debug_file, mode='w')
        debug_handler.setLevel(logging.DEBUG)
        
        # Very detailed format
        debug_format = logging.Formatter(
            '%(asctime)s.%(msecs)03d | %(process)d:%(thread)d | '
            '%(name)s | %(levelname)s | %(pathname)s:%(funcName)s:%(lineno)d | '
            '%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        debug_handler.setFormatter(debug_format)
        self.logger.addHandler(debug_handler)
        
    def get_child_logger(self, component: str) -> 'ComponentLogger':
        """Get a logger for a specific component"""
        return ComponentLogger(self, component)
        
    def log_agent_activity(self, agent_id: str, activity: str, details: Dict[str, Any] = None):
        """Log agent-specific activity"""
        if agent_id not in self.agent_logs:
            self.agent_logs[agent_id] = []
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "details": details or {}
        }
        
        self.agent_logs[agent_id].append(entry)
        self.activity_log.append({"agent_id": agent_id, **entry})
        
        # Also log to main logger
        self.logger.info(f"Agent[{agent_id[:8]}] {activity}")
        if details:
            self.logger.debug(f"Details: {json.dumps(details, indent=2)}")
            
    def log_error(self, error: Exception, context: str = ""):
        """Log an error with full traceback"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        self.error_log.append(error_entry)
        
        # Log to file
        self.logger.error(f"{context}: {type(error).__name__}: {error}")
        self.logger.debug(f"Traceback:\n{error_entry['traceback']}")
        
        # Save error to separate file
        error_file = self.log_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump(error_entry, f, indent=2)
            
    def log_command(self, command: str, source: str = "user"):
        """Log a command execution"""
        self.logger.info(f"Command from {source}: {command}")
        self.activity_log.append({
            "timestamp": datetime.now().isoformat(),
            "type": "command",
            "source": source,
            "command": command
        })
        
    def log_system_event(self, event: str, details: Dict[str, Any] = None):
        """Log a system event"""
        self.logger.info(f"System Event: {event}")
        if details:
            self.logger.debug(f"Event Details: {json.dumps(details, indent=2)}")
            
        self.activity_log.append({
            "timestamp": datetime.now().isoformat(),
            "type": "system_event",
            "event": event,
            "details": details or {}
        })
        
    def get_recent_activity(self, limit: int = 50) -> list:
        """Get recent activity log entries"""
        return self.activity_log[-limit:]
        
    def get_agent_log(self, agent_id: str) -> list:
        """Get logs for a specific agent"""
        return self.agent_logs.get(agent_id, [])
        
    def save_session_log(self):
        """Save complete session log"""
        session_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        session_data = {
            "start_time": self.activity_log[0]["timestamp"] if self.activity_log else None,
            "end_time": datetime.now().isoformat(),
            "total_activities": len(self.activity_log),
            "total_errors": len(self.error_log),
            "total_audit_entries": len(self.audit_log),
            "agent_count": len(self.agent_logs),
            "activity_log": self.activity_log,
            "error_log": self.error_log,
            "audit_log": self.audit_log,
            "agent_logs": self.agent_logs
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        self.logger.info(f"Session log saved to: {session_file}")
        
    def _log_audit_entry(self, level: str, message: str):
        """Log an audit entry"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "context": "system_audit"
        }
        self.audit_log.append(audit_entry)
        
        # Also log to audit file
        if hasattr(self, 'audit_logger'):
            getattr(self.audit_logger, level.lower())(message)
    
    def debug(self, message: str, audit: bool = False):
        """Log debug message"""
        self.logger.debug(message)
        if audit:
            self._log_audit_entry("DEBUG", message)
        
    def info(self, message: str, audit: bool = False):
        """Log info message"""
        self.logger.info(message)
        if audit:
            self._log_audit_entry("INFO", message)
        
    def warning(self, message: str, audit: bool = False):
        """Log warning message"""
        self.logger.warning(message)
        if audit:
            self._log_audit_entry("WARNING", message)
        
    def error(self, message: str, audit: bool = False):
        """Log error message"""
        self.logger.error(message)
        if audit:
            self._log_audit_entry("ERROR", message)
        
    def critical(self, message: str, audit: bool = False):
        """Log critical message"""
        self.logger.critical(message)
        if audit:
            self._log_audit_entry("CRITICAL", message)
    
    def get_audit_log(self, limit: int = 100) -> list:
        """Get recent audit log entries"""
        return self.audit_log[-limit:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            "total_activities": len(self.activity_log),
            "total_errors": len(self.error_log),
            "total_audit_entries": len(self.audit_log),
            "agent_count": len(self.agent_logs),
            "agents": {
                "active": len([agent for agent in self.agent_logs.keys()]),
                "total_tasks_completed": sum(len(logs) for logs in self.agent_logs.values())
            },
            "recent_activity": self.get_recent_activity(10),
            "recent_errors": self.error_log[-5:] if self.error_log else [],
            "recent_audit": self.get_audit_log(10),
            "log_files": {
                "main_log": str(self.log_dir / "latest.log"),
                "debug_log": str(self.log_dir / "debug.log"),
                "audit_log": str(self.log_dir / "audit.log")
            }
        }

class ComponentLogger:
    """Logger for specific components"""
    
    def __init__(self, parent_logger: NexusLogger, component: str):
        self.parent = parent_logger
        self.component = component
        self.logger = logging.getLogger(f"{parent_logger.name}.{component}")
        
    def debug(self, message: str, audit: bool = False):
        self.logger.debug(f"[{self.component}] {message}")
        if audit:
            self.parent._log_audit_entry("DEBUG", f"[{self.component}] {message}")
        
    def info(self, message: str, audit: bool = False):
        self.logger.info(f"[{self.component}] {message}")
        if audit:
            self.parent._log_audit_entry("INFO", f"[{self.component}] {message}")
        
    def warning(self, message: str, audit: bool = False):
        self.logger.warning(f"[{self.component}] {message}")
        if audit:
            self.parent._log_audit_entry("WARNING", f"[{self.component}] {message}")
        
    def error(self, message: str, audit: bool = False):
        self.logger.error(f"[{self.component}] {message}")
        if audit:
            self.parent._log_audit_entry("ERROR", f"[{self.component}] {message}")
        
    def log_activity(self, activity: str, details: Dict[str, Any] = None):
        """Log component activity"""
        self.parent.activity_log.append({
            "timestamp": datetime.now().isoformat(),
            "component": self.component,
            "activity": activity,
            "details": details or {}
        })
        self.info(activity)

# Global logger instance
_nexus_logger = None

def get_logger(name: str = "NEXUS") -> NexusLogger:
    """Get or create the global logger instance"""
    global _nexus_logger
    if _nexus_logger is None:
        _nexus_logger = NexusLogger(name)
    return _nexus_logger

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        func_name = f"{func.__module__}.{func.__name__}"
        
        logger.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func_name} returned: {result}")
            return result
        except Exception as e:
            logger.log_error(e, f"Error in {func_name}")
            raise
            
    return wrapper

# Example usage and testing
if __name__ == "__main__":
    # Initialize logger
    logger = get_logger()
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test component logger
    stage_logger = logger.get_child_logger("StageManager")
    stage_logger.info("Stage Manager initialized")
    stage_logger.log_activity("Created new agent", {"agent_id": "abc123", "type": "developer"})
    
    # Test agent activity
    logger.log_agent_activity("agent-001", "Started task", {"task": "Build API"})
    logger.log_agent_activity("agent-001", "Completed step", {"step": 1, "description": "Setup Flask"})
    
    # Test error logging
    try:
        1 / 0
    except Exception as e:
        logger.log_error(e, "Testing error logging")
        
    # Test command logging
    logger.log_command("create agent for web scraping", "user")
    
    # Test system event
    logger.log_system_event("System startup", {"version": "2.0", "modules": ["stage", "desktop", "chat"]})
    
    # Save session
    logger.save_session_log()
    
    print(f"\nLogs saved to: {logger.log_dir}")
    print(f"Check latest.log for the most recent log file")