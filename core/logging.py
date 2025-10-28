# logging.py - enhanced version for MicroPython with file logging
import time
import os

DEBUG = 10
INFO = 20
WARN = 30
ERROR = 40
CRITICAL = 50

_level_names = {
    DEBUG: 'DEBUG',
    INFO: 'INFO', 
    WARN: 'WARNING',
    ERROR: 'ERROR',
    CRITICAL: 'CRITICAL'
}

# Global configuration
_log_config = {
    'filename': None,
    'level': INFO,
    'format': '[%(asctime)s][%(levelname)s][%(name)s] %(message)s',
    'filemode': 'a'
}

class Logger:
    def __init__(self, name):
        self.name = name
        self.level = _log_config['level']
        self._file = None
        
        # Open log file if configured
        if _log_config['filename']:
            try:
                self._file = open(_log_config['filename'], _log_config['filemode'])
            except Exception as e:
                print(f"Failed to open log file: {e}")
    
    def setLevel(self, level):
        self.level = level
    
    def _format_message(self, level, msg, *args):
        """Format message according to the format string"""
        if args:
            formatted_msg = msg % args
        else:
            formatted_msg = msg
            
        # Get current time
        current_time = time.time()
        year, month, day, hour, minute, second, weekday, yearday = time.localtime(current_time)
        asctime = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
        
        # Replace placeholders in format string
        formatted = _log_config['format']
        formatted = formatted.replace('%(asctime)s', asctime)
        formatted = formatted.replace('%(levelname)s', _level_names[level])
        formatted = formatted.replace('%(name)s', self.name)
        formatted = formatted.replace('%(message)s', formatted_msg)
        formatted = formatted.replace('%(threadName)s', 'main')  # MicroPython doesn't have threads
        
        return formatted
    
    def log(self, level, msg, *args):
        if level >= self.level:
            formatted_msg = self._format_message(level, msg, *args)
            
            # Print to console
            print(formatted_msg)
            
            # Write to file if available
            if self._file:
                self._file.write(formatted_msg + '\n')
                self._file.flush()  # Ensure data is written to storage
    
    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)
    
    def info(self, msg, *args):
        self.log(INFO, msg, *args)
    
    def warning(self, msg, *args):
        self.log(WARN, msg, *args)
    
    def error(self, msg, *args):
        self.log(ERROR, msg, *args)
    
    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)
    
    def close(self):
        """Close log file"""
        if self._file:
            self._file.close()
            self._file = None

def getLogger(name=None):
    return Logger(name or 'root')

def basicConfig(filename=None, level=INFO, format=None, filemode='a'):
    """Configure logging similar to standard logging.basicConfig"""
    _log_config['filename'] = filename
    _log_config['level'] = level
    _log_config['filemode'] = filemode
    
    if format:
        _log_config['format'] = format
    
    # If filename is provided, ensure directory exists
    if filename:
        try:
            # Extract directory path
            dir_path = '/'.join(filename.split('/')[:-1])
            if dir_path and not _exists(dir_path):
                _makedirs(dir_path)
        except Exception as e:
            print(f"Warning: Could not create log directory: {e}")

def _exists(path):
    """Check if path exists"""
    try:
        os.listdir(path)
        return True
    except OSError:
        return False

def _makedirs(path):
    """Create directory recursively"""
    parts = path.split('/')
    current_path = ''
    for part in parts:
        if part:
            current_path += '/' + part if current_path else part
            try:
                os.mkdir(current_path)
            except OSError:
                pass  # Directory might already exist

# Convenience functions
def debug(msg, *args):
    getLogger().debug(msg, *args)

def info(msg, *args):
    getLogger().info(msg, *args)

def warning(msg, *args):
    getLogger().warning(msg, *args)

def error(msg, *args):
    getLogger().error(msg, *args)

def critical(msg, *args):
    getLogger().critical(msg, *args)