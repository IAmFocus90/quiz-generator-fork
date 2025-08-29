import logging
from email.mime.text import MIMEText

from server.celery_config import celery_app
from .share_email_utils import compose_quiz_email, send_email, sender_email

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@celery_app.task(name="tasks.send_quiz_email")
def send_quiz_email(quiz_title: str, quiz_description: str, recipient: str, shareable_link: str):
    """
    Existing quiz-link email task (kept for backward compatibility).
    """
    try:
        message = compose_quiz_email(recipient, quiz_title, quiz_description, shareable_link)
        send_email(recipient, message)
        logger.info(f"[Celery Task] Completed send_quiz_email for {recipient}")
    except Exception as e:
        logger.error(f"[Celery Task Error] Unexpected failure in send_quiz_email task: {e}", exc_info=True)
        raise


@celery_app.task(name="tasks.send_email_generic")
def send_email_generic(recipient: str, subject: str, body: str):
    """
    New generic task used by the platform email service for ANY template/purpose.
    """
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient

        send_email(recipient, msg)
        logger.info(f"[Celery Task] Completed send_email_generic for {recipient}")
    except Exception as e:
        logger.error(f"[Celery Task Error] Failure in send_email_generic: {e}", exc_info=True)
        raise









# import logging
# from server.celery_config import celery_app
# from .share_email_utils import compose_quiz_email, send_email
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)


# @celery_app.task(name="tasks.send_quiz_email")
# def send_quiz_email(quiz_title: str, quiz_description: str, recipient: str, shareable_link: str):
#     try:
#         message = compose_quiz_email(recipient, quiz_title, quiz_description, shareable_link)
#         send_email(recipient, message)

#         logger.info(f"[Celery Task] Completed send_quiz_email for {recipient}")
#     except Exception as e:
#         logger.error(f"[Celery Task Error] Unexpected failure in send_quiz_email task: {e}", exc_info=True)
#         raise

