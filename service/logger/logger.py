import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("output/log/app.log", encoding='utf-8'),
        logging.StreamHandler()  # чтобы видеть и в консоли при разработке
    ]
)
logger = logging.getLogger(__name__)

def get_log_writer(log_path: str = None):
    """Возвращает функцию для записи в логгер и (опционально) в файл."""
    def write(msg: str):
        logger.info(msg)
        if log_path:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
    return write