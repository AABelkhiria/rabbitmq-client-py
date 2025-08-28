from setuptools import setup, find_packages

setup(
    name="rabbitmq-client",
    version="0.2.0",
    description="Singleton RabbitMQ client with modular structure and retry logic.",
    author="Belkhiria Ash",
    author_email="belkhiria.achraf@gmail.com",
    url="https://github.com/AABelkhiria/rabbitmq-client-py",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pika>=1.3.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
