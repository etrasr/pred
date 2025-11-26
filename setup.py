from setuptools import setup, find_packages

setup(
    name="keno-prediction-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy==1.21.6",
        "python-telegram-bot==13.15", 
        "flask==2.0.3",
    ],
    python_requires=">=3.7,<3.12",
)
