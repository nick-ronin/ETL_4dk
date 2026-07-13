import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("output/log/pipeline.log", encoding='utf-8'),
        logging.StreamHandler()  # чтобы видеть и в консоли при разработке
    ]
)
logger = logging.getLogger(__name__)