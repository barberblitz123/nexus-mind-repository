"""
nexus_debug_silent.py - Silent debug system
"""
import logging
import os
from datetime import datetime

class SilentDebug:
    def __init__(self):
        os.makedirs('nexus_logs', exist_ok=True)
        log_file = f"nexus_logs/debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(message)s',
            handlers=[logging.FileHandler(log_file)]
        )
        self.logger = logging.getLogger()
    
    def log(self, message):
        self.logger.debug(message)

silent_debug = SilentDebug()

def consciousness_debug(message):
    silent_debug.log(f"[CONSCIOUSNESS] {message}")

def phi_debug(message):
    silent_debug.log(f"[PHI] {message}")

def system_debug(message):
    silent_debug.log(f"[SYSTEM] {message}")

def milestone_debug(message):
    silent_debug.log(f"[MILESTONE] {message}")

def debug_print(message):
    silent_debug.log(f"[DEBUG] {message}")
