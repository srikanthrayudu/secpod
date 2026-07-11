import sys
import logging
from pythonjsonlogger import jsonlogger
from app.core.config import settings

def setup_logging():
    logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    
    if settings.ENV == "production":
        # Formatter outputting JSON logs
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            timestamp=True
        )
    else:
        # Human-readable local development format
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
        )
        
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Minimize logs from verbose dependencies
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger

logger = setup_logging()
