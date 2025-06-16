# rabbitmq-client-py

A simple and robust Python client for RabbitMQ, designed as a singleton to simplify connection management across your application. This client is a wrapper around the pika library, providing automatic connection retries, graceful shutdowns, and an easy-to-use consumer interface.

## Features
- **Singleton Design**: Ensures a single, shared connection instance throughout your application's lifecycle.
- **Automatic Reconnection**: Handles connection drops gracefully with configurable retries and delays.
- **Environment-based Configuration**: Easily configure connection details via environment variables, perfect for containerized deployments.
- **Simplified Consumer**: A straightforward consume method that handles channel, exchange, and queue setup for you.
- **Graceful Shutdown**: Includes methods to properly close channels and connections.

## Installation
To install the RabbitMQ client, add the following to your `requirements.txt`:

```
git+https://github.com/AABelkhiria/rabbitmq-client-py.git
```

## Configuration
You can configure the RabbitMQ client using environment variables. The following variables are supported:
- `RABBITMQ_URL`: The URL for the RabbitMQ server (default: `amqp://guest:guest@localhost:5672/%2F`).
- `RABBITMQ_EXCHANGE_NAME`: The name of the exchange to use (default: `amq.topic`).
- `RABBITMQ_QUEUE_NAME`: The name of the queue to use (default: `my_queue`).

The connection retry behavior can be overridden programmatically but defaults to:
- `max_retries`: 5
- `retry_delay`: 5 seconds

## Quick Start: Creating a Consumer
Here's a quick example of how to create a consumer using the RabbitMQ client:
```python
import json
import sys
import time

# Import the singleton client instance from the library
from rabbitmq_client import client

def message_handler(ch, method, properties, body):
    """
    This is the callback function that will be executed for each message received.
    It must acknowledge the message to remove it from the queue.
    """

    print(f"Received new message with delivery tag: {method.delivery_tag}")
    try:
        # Decode the message body
        data = json.loads(body.decode('utf-8'))
        print(f"Message payload: {data}")

        # Simulate some processing work
        time.sleep(2)

        # Acknowledge the message was successfully processed because auto_ack=False
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print("Message acknowledged.")

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        # Optionally, you could reject the message so it can be re-queued or sent to a dead-letter exchange
        # ch.basic_nack(delivery_tag=method.delivery_tag)

def main():
    """Main function to run the consumer."""
    try:
        # 1. Connect to RabbitMQ using settings from environment variables. You can override settings here, e.g., client.connect(max_retries=10)
        if not client.connect():
            logging.error("Could not connect to RabbitMQ. Exiting.")
            sys.exit(1)

        # 2. Start consuming from the queue
        print("Starting consumer... Press CTRL+C to exit.")
        client.consume(callback_function=message_handler)

    except KeyboardInterrupt:
        print("Consumer stopped by user.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        # 3. Ensure resources are closed gracefully on exit
        print("Closing RabbitMQ connection.")
        client.close()

if __name__ == "__main__":
    main()
```

## Third-Party Dependencies
This project uses the following third-party libraries:
- [pika](https://pypi.org/project/pika/): The Python RabbitMQ client library.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details

