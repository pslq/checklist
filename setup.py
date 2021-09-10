#!/usr/bin/env python3
import setuptools, sys

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

if sys.version_info[:2] < (3, 7):
  raise RuntimeError("Python version >= 3.7 required.")

setuptools.setup(
    name="checklist-aix",
    version="0.0.1",
    author="Paulo Queiroz",
    author_email="paulo.sergio.lemes.queiroz@gmail.com",
    description="An Python script to collect performance data from AIX servers and store into a influxDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    platforms=["Linux", "AIX", "Unix"],
    packages=['pq_checklist'],
    url="https://github.com/pslq/checklist-aix",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires = [ "ansible-runner", "configparser", "asyncio", "influxdb_client" ],
    python_requires=">=3.7",
    entry_points={
      'console_scripts': 'pq_checklist = pq_checklist:main'
    },
)
