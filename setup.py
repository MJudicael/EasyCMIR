from setuptools import setup, find_packages

setup(
    name="easycmir",
    version="1.4",
    packages=find_packages(),
    install_requires=[
        'PySide6',
        'requests',
        'beautifulsoup4',
    ],
)