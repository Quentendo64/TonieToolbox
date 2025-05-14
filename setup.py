#!/usr/bin/env python3
"""
Setup script for TonieToolbox.
"""

import os
from setuptools import setup, find_packages

with open(os.path.join('TonieToolbox', '__init__.py'), 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip("'\"")
            break
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="TonieToolbox",
    version=version,
    author="Quentendo64",
    author_email="quentin@wohlfeil.at",
    description="Convert audio files to Toniebox compatible format (.TAF) and interact with TeddyCloud.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Quentendo64/TonieToolbox",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
    ],
    python_requires=">=3.6",
    install_requires=[
        "protobuf<=3.19.0",
        "requests>=2.32.3",
        "mutagen>=1.47.0",
        "packaging>=25.0",
        "tqdm>=4.67.1"
    ],
    entry_points={
        'console_scripts': [
            'tonietoolbox=TonieToolbox.__main__:main',
        ],
    },
    include_package_data=True,
)