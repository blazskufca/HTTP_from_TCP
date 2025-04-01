from setuptools import find_packages, setup

setup(
    name="tcp_to_http",
    version="0.0.1",
    description="A simple Golang style HTTP server implementation in Python",
    author="Blaž Škufca",
    author_email="3877198+blazskufca@users.noreply.github.com",
    packages=find_packages(),
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
