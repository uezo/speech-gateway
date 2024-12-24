from setuptools import setup, find_packages

setup(
    name="speech_gateway",
    version="0.1.1",
    url="https://github.com/uezo/speech-gateway",
    author="uezo",
    author_email="uezo@uezo.net",
    maintainer="uezo",
    maintainer_email="uezo@uezo.net",
    description="A reverse proxy server that enhances speech synthesis with essential, extensible features. 🦉💬",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests*"]),
    install_requires=["aiofiles==24.1.0", "fastapi==0.115.6", "httpx==0.28.1", "uvicorn==0.34.0"],
    license="Apache v2",
    classifiers=[
        "Programming Language :: Python :: 3"
    ]
)
