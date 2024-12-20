import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Configure logging to both console and file"""
    # Create logs directory if it doesn't exist
    log_dir = Path("output/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create unique log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"video_creator_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Logging initialized. Log file: {log_file}")
    return logging.getLogger(__name__)
