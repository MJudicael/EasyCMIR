from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    install_requires=[
        'PySide6',
        'requests',
        'beautifulsoup4',
    ],
)