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
        logger.info(f"RabbitMQClient initialized with URL: {self.rabbitmq_url}")

    def connect(
        self,
        rabbitmq_url=None,
        exchange_name=None,
        queue_name=None,
        max_retries=None,
        retry_delay=None,
    ):
        self.rabbitmq_url = rabbitmq_url or self.rabbitmq_url
        self.exchange_name = exchange_name or self.exchange_name
        self.queue_name = queue_name or self.queue_name
        self.max_retries = max_retries or self.max_retries
        self.retry_delay = retry_delay or self.retry_delay

        self._close_resources()

        self.connection, self.channel = _connection.establish_connection(
            self.rabbitmq_url, self.max_retries, self.retry_delay
        )
        return self.connection is not None and self.channel is not None

    def get_channel(self):
        if not self.channel or self.channel.is_closed:
            logger.warning("Channel closed or unavailable, reconnecting...")
            if not self.connect():
                raise ConnectionError("Failed to connect and get a channel after retries.")

        return self.channel

    def consume(self, callback_function, queue_name=None, exchange_type="direct", routing_key=""):
        queue_name = queue_name or self.queue_name
        try:
            channel = self.get_channel()

            logger.info(f"Declaring exchange '{self.exchange_name}' of type '{exchange_type}'")
            channel.exchange_declare(exchange=self.exchange_name, exchange_type=exchange_type)

            logger.info(f"Declaring queue '{queue_name}' (durable=True)")
            result = channel.queue_declare(queue=queue_name)

            logger.info(f"Binding queue '{result.method.queue}' to exchange '{self.exchange_name}'")
            channel.queue_bind(exchange=self.exchange_name, queue=queue_name, routing_key=routing_key)

            channel.basic_qos(prefetch_count=self.prefetch_count)

            logger.info(f"Waiting for messages on queue '{queue_name}'.")
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
        _connection.close_resources(self.connection, self.channel)
        self.connection = None
        self.channel = None

    def close(self):
        logger.info("Closing RabbitMQ client resources.")
        self._close_resources()
