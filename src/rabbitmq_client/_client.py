import logging
from threading import Lock

from . import _config, _connection

logger = logging.getLogger(__name__)


class RabbitMQClient:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.connection = None
        self.channel = None
        self.rabbitmq_url = _config.RABBITMQ_URL
        self.exchange_name = _config.EXCHANGE_NAME
        self.queue_name = _config.QUEUE_NAME
        self.max_retries = _config.MAX_RETRIES
        self.retry_delay = _config.RETRY_DELAY
        self.prefetch_count = _config.DEFAULT_PREFETCH_COUNT

        self._initialized = True
        logger.debug(f"RabbitMQClient initialized with URL: {self.rabbitmq_url}")

    def connect(
        self,
        rabbitmq_url: str = _config.RABBITMQ_URL,
        exchange_name: str = _config.EXCHANGE_NAME,
        queue_name: str = _config.QUEUE_NAME,
        max_retries: int = _config.MAX_RETRIES,
        retry_delay: int = _config.RETRY_DELAY,
    ) -> bool:
        """
        Establish a connection to RabbitMQ and set up the channel.

        Args:
            rabbitmq_url (str, optional): RabbitMQ connection URL. Defaults to 'amqp://guest:guest@localhost:5672/%2F'.
            exchange_name (str, optional): Exchange name to use.  Defaults to 'amq.topic'.
            queue_name (str, optional):  Queue name to use. Defaults to 'my_queue'.
            max_retries (int, optional): Maximum number of retries for connection attempts. Defaults to 5.
            retry_delay (int, optional): Delay between retries in seconds. Defaults to 5.

        Returns:
            bool: True if connection and channel are established successfully, False otherwise.
        """

        logger.debug("Connecting to RabbitMQ...")
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._close_resources()

        self.connection, self.channel = _connection.establish_connection(
            self.rabbitmq_url, self.max_retries, self.retry_delay
        )
        return self.connection is not None and self.channel is not None

    def get_channel(self) -> "pika.channel.Channel":
        """
        Get the RabbitMQ channel, reconnecting if necessary.

        Raises:
            ConnectionError: If the channel is closed or unavailable, and reconnection fails.

        Returns:
            Channel: The RabbitMQ channel object.
        """

        if not self.channel or self.channel.is_closed:
            logger.warning("Channel closed or unavailable, reconnecting...")
            if not self.connect():
                raise ConnectionError("Failed to connect and get a channel after retries.")

        return self.channel
    
    def send_message(
        self,
        message: str,
        exchange_name: str = "",
        routing_key: str = "",
        exchange_type: str = "direct",
    ):
        """
        Send a message to a RabbitMQ exchange.

        Args:
            message (str): The message content to send.
            exchange_name (str, optional): The name of the exchange to send the message to. Defaults to the instance's exchange_name.
            routing_key (str, optional): The routing key for the message. Defaults to an empty string.
            exchange_type (str, optional): The type of exchange to declare. Defaults to 'direct'.
        """
        exchange_name = exchange_name or self.exchange_name
        try:
            channel = self.get_channel()

            logger.debug(
                f"Declaring exchange '{exchange_name}' of type '{exchange_type}'"
            )
            channel.exchange_declare(
                exchange=exchange_name, exchange_type=exchange_type
            )

            logger.debug(
                f"Publishing message to exchange '{exchange_name}' with routing key '{routing_key}'"
            )
            channel.basic_publish(
                exchange=exchange_name, routing_key=routing_key, body=message
            )
            logger.debug(
                f"Message published to exchange '{exchange_name}' with routing key '{routing_key}'"
            )

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._close_resources()
            raise

    def consume(
        self,
        callback_function: callable,
        queue_name: str = "",
        exchange_type: str = "direct",
        routing_key: str = "",
    ):
        """
        Consume messages from a RabbitMQ queue and process them with the provided callback function.

        Args:
            callback_function (callable):  The function to call when a message is received.
            queue_name (str, optional): The name of the queue to consume from. Defaults to the instance's queue_name.
            exchange_type (str, optional): The type of exchange to declare. Defaults to 'direct'.
            routing_key (str, optional): The routing key to use for binding the queue to the exchange. Defaults to an empty string.
        """

        queue_name = queue_name or self.queue_name
        try:
            channel = self.get_channel()

            logger.debug(f"Declaring exchange '{self.exchange_name}' of type '{exchange_type}'")
            channel.exchange_declare(exchange=self.exchange_name, exchange_type=exchange_type)

            logger.debug(f"Declaring queue '{queue_name}' (durable=True)")
            result = channel.queue_declare(queue=queue_name)

            logger.debug(f"Binding queue '{result.method.queue}' to exchange '{self.exchange_name}'")
            channel.queue_bind(exchange=self.exchange_name, queue=queue_name, routing_key=routing_key)

            channel.basic_qos(prefetch_count=self.prefetch_count)

            logger.debug(f"Waiting for messages on queue '{queue_name}'.")
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback_function,
                auto_ack=False,
            )

            channel.start_consuming()

        except Exception as e:
            logger.error(f"Error during consume: {e}")
            self._close_resources()
            raise

    def _close_resources(self):
        """
        Close the RabbitMQ connection and channel resources.
        """

        _connection.close_resources(self.connection, self.channel)
        self.connection = None
        self.channel = None

    def close(self):
        """
        Close the RabbitMQ client resources gracefully.
        """

        logger.debug("Closing RabbitMQ client resources.")
        self._close_resources()
