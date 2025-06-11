import logging
import time

import pika

logger = logging.getLogger(__name__)


def establish_connection(
    rabbitmq_url: str,
    max_retries: int,
    retry_delay: int,
) -> tuple[pika.BlockingConnection, pika.channel.Channel]:
    """
    Establish a connection to RabbitMQ with retry logic.

    Args:
        rabbitmq_url (str): The RabbitMQ connection URL.
        max_retries (int): Maximum number of connection attempts before giving up.
        retry_delay (int): Delay in seconds between retries.

    Returns:
        tuple: A tuple containing the connection and channel objects if successful, or (None, None) if failed.
    """

    params = pika.URLParameters(rabbitmq_url)
    attempts = 0

    while attempts < max_retries:
        try:
            logger.info(f"Attempting to connect to RabbitMQ (attempt {attempts + 1}/{max_retries}) at {rabbitmq_url}")
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            logger.info("Successfully connected to RabbitMQ and opened a channel.")
            return connection, channel

        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")

        attempts += 1
        if attempts < max_retries:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

    logger.error("Max retries reached. Could not connect to RabbitMQ.")
    return None, None


def close_resources(connection: pika.BlockingConnection, channel):
    """
    Close the RabbitMQ connection and channel gracefully.

    Args:
        connection (BlockingConnection): The RabbitMQ connection object.
        channel: The RabbitMQ channel object.
    """

    try:
        if channel and channel.is_open:
            channel.close()
            logger.info("RabbitMQ channel closed.")
    except Exception as e:
        logger.error(f"Error closing RabbitMQ channel: {e}")

    try:
        if connection and connection.is_open:
            connection.close()
            logger.info("RabbitMQ connection closed.")
    except Exception as e:
        logger.error(f"Error closing RabbitMQ connection: {e}")
