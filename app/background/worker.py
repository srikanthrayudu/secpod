from celery import Celery
from app.core.config import settings
from app.utils.logger import logger

# Initialize Celery Application
celery_app = Celery(
    "background_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Standard Configurations
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="tasks.send_welcome_email")
def send_welcome_email(email: str, name: str) -> str:
    logger.info(f"[Celery Task] Sending welcome email to {name} <{email}>")
    # Simulation
    return f"Welcome email sent to {email}"

@celery_app.task(name="tasks.process_document_embedding")
def process_document_embedding(doc_id: str, content: str) -> str:
    logger.info(f"[Celery Task] Processing text embedding index for document {doc_id}")
    # Simulation
    return f"Document {doc_id} indexed in background"
