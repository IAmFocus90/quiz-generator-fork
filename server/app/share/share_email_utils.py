import os
import logging
import smtplib
import time
import socket
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Custom Env Loader
def require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"[Config Error] Required environment variable '{var_name}' is missing.")
    return value

sender_email = require_env("SENDER_EMAIL")
sender_password = require_env("SENDER_PASSWORD")
email_host = require_env("EMAIL_HOST")
email_port = int(require_env("EMAIL_PORT"))

# Retry configuration (To Do: Migrate to envars later)
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds
SMTP_TIMEOUT = 20  # seconds


def compose_quiz_email(recipient: str, title: str, description: str, shareable_link: str) -> MIMEText:
    subject = f"Check out this quiz: {title}"
    body = (
        f"Here's a quiz we thought you'd like:\n\n"
        f"Title: {title}\n"
        f"Description: {description}\n"
        f"Access it here: {shareable_link}\n\nEnjoy!"
    )

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient
    return message


def send_email(recipient: str, message: MIMEText) -> None:
    attempt = 0

    while attempt < MAX_RETRIES:
        try:
            with smtplib.SMTP(email_host, email_port, timeout=SMTP_TIMEOUT) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient, message.as_string())

            logger.info(f"[Email] Email successfully sent to {recipient}")
            return

        except (smtplib.SMTPException, socket.timeout, ConnectionRefusedError) as e:
            attempt += 1
            logger.warning(
                f"[Email Retry] Attempt {attempt}/{MAX_RETRIES} failed for {recipient}: {e}"
            )

            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * attempt
                logger.info(f"[Email Retry] Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(
                    f"[Email Error] All {MAX_RETRIES} attempts failed for {recipient}.", exc_info=True
                )
                raise
