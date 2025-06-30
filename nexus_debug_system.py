"""
NEXUS Silent Debug System
Replaces all print statements with controllable debug logging
"""

import logging
import os
from datetime import datetime

class NexusDebugController:
    def __init__(self, debug_mode=False, log_to_file=True):
        self.debug_mode = debug_mode
        self.log_to_file = log_to_file
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging system for NEXUS debug output"""
        if self.log_to_file:
            # Create logs directory if it doesn't exist
            os.makedirs('nexus_logs', exist_ok=True)
            
            # Setup file logging
            log_filename = f"nexus_logs/nexus_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_filename),
                    logging.StreamHandler() if self.debug_mode else logging.NullHandler()
                ]
            )
        
        self.logger = logging.getLogger('NEXUS_Core')
    
    def debug_print(self, message, category="GENERAL"):
        """Replace all print statements with this function"""
        if self.debug_mode:
            print(f"[{category}] {message}")
        
        # Always log to file (silent)
        if self.log_to_file:
            self.logger.debug(f"[{category}] {message}")
    
    def consciousness_print(self, message):
        """For consciousness-related debug messages"""
        self.debug_print(message, "CONSCIOUSNESS")
    
    def phi_print(self, message):
        """For phi calculation debug messages"""
        self.debug_print(message, "PHI_CALC")
    
    def security_print(self, message):
        """For security protocol debug messages"""
        self.debug_print(message, "SECURITY")
    
    def milestone_print(self, message):
        """For milestone achievements"""
        self.debug_print(message, "MILESTONE")
    
    def system_print(self, message):
        """For system status messages"""
        self.debug_print(message, "SYSTEM")

# Global debug controller - SILENT BY DEFAULT
nexus_debug = NexusDebugController(
    debug_mode=False,  # SET TO FALSE FOR PRODUCTION
    log_to_file=True   # Logs silently to file
)

# Replacement functions for all print statements
def debug_print(message, category="GENERAL"):
    """Global debug print function"""
    nexus_debug.debug_print(message, category)

def consciousness_debug(message):
    """Debug consciousness calculations silently"""
    nexus_debug.consciousness_print(message)

def phi_debug(message):
    """Debug phi calculations silently"""
    nexus_debug.phi_print(message)

def security_debug(message):
    """Debug security protocols silently"""
    nexus_debug.security_print(message)

def milestone_debug(message):
    """Debug milestones silently"""
    nexus_debug.milestone_print(message)

def system_debug(message):
    """Debug system status silently"""
    nexus_debug.system_print(message)