"""
Utilities for log management in the Nasdaq Stock Assistant application.
"""
import os
import logging
import datetime
import shutil
from pathlib import Path

def setup_logging(app_name="nasdaq_assistant", log_level=logging.INFO, max_logs=10):
    """
    Set up logging with both console and file output.
    
    Args:
        app_name: Name prefix for the log file
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        max_logs: Maximum number of log files to keep
    
    Returns:
        logger: Configured logger
    """
    # Create log directory
    log_dir = Path('./log')
    log_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"{app_name}_{timestamp}.log"
    log_filepath = log_dir / log_filename
    
    # Configure logger
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(log_level)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Clean up old logs
    cleanup_old_logs(log_dir, max_logs)
    
    logger.info(f"Logging initialized. Logs will be saved to {log_filepath}")
    return logger

def cleanup_old_logs(log_dir, max_logs):
    """
    Delete old log files when the number exceeds max_logs.
    
    Args:
        log_dir: Directory containing log files
        max_logs: Maximum number of log files to keep
    """
    try:
        log_files = list(log_dir.glob('*.log'))
        if len(log_files) > max_logs:
            # Sort by modification time (oldest first)
            log_files.sort(key=lambda x: os.path.getmtime(x))
            
            # Delete oldest logs
            for old_file in log_files[:len(log_files) - max_logs]:
                old_file.unlink()
                
    except Exception as e:
        print(f"Error cleaning up old logs: {e}")

def archive_logs(archive_dir="./log_archive"):
    """
    Archive log files to a zip file.
    
    Args:
        archive_dir: Directory to store archive files
    """
    try:
        log_dir = Path('./log')
        if not log_dir.exists():
            return
            
        # Create archive directory
        archive_path = Path(archive_dir)
        archive_path.mkdir(exist_ok=True)
        
        # Create archive filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_file = archive_path / f"logs_archive_{timestamp}.zip"
        
        # Create zip file
        shutil.make_archive(
            str(archive_file).replace('.zip', ''), 
            'zip', 
            log_dir
        )
        
        print(f"Logs archived to {archive_file}")
    except Exception as e:
        print(f"Error archiving logs: {e}")

if __name__ == "__main__":
    # If run directly, perform log maintenance
    archive_logs()
    cleanup_old_logs(Path('./log'), 10)
    print("Log maintenance completed.")
