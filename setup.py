#!/usr/bin/env python
from setuptools import setup

setup(
    name="Mimir",
    version="0.1.1",
    description="Custom database",
    author="Korbinian Schweiger",
    author_email="korbinian.schweiger@gmail.com",
    licence="MIT",
    packages=["mimir"],
    scripts=["bin/runMTF.py"],
)
