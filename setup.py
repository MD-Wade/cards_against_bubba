# setup.py
from setuptools import setup, find_packages

setup(
    name="cards_against_bubba",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "py-cord>=2.0.0",
        # ...other deps
    ],
)
