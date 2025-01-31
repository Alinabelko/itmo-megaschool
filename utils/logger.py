import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger():
    logger = logging.getLogger('app_logger')
    
    # Проверяем, не был ли уже настроен логгер
    if logger.handlers:
        return logger
        
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760, 
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
