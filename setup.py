from setuptools import setup, find_packages

setup(
    name="rabbitmq-client",
    version="0.1.0",
    description="Singleton RabbitMQ client with modular structure and retry logic.",
    author="Belkhiria Ash",
    author_email="belkhiria.achraf@gmail.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pika>=1.3.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
