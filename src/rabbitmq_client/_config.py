import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
EXCHANGE_NAME = os.getenv("RABBITMQ_EXCHANGE_NAME", "amq.topic")
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE_NAME", "my_queue")

MAX_RETRIES = 5
RETRY_DELAY = 5
DEFAULT_PREFETCH_COUNT = 1
