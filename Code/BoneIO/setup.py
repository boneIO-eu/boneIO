#!/usr/bin/env python
# -*- coding:utf-8 -*-
from setuptools import setup, find_packages

with open("bone/version.py") as f:
    exec(f.read())

setup(
    name="boneIO",
    version=__version__,  # type: ignore # noqa: F821,
    description="Python Helper for BoneIO",
    long_description="Python Helper for BoneIO",
    long_description_content_type="text/markdown",
    url="https://github.com/maciejk1984/boneIO",
    download_url="https://github.com/bosch-thermostat/bosch-thermostat-client-python/archive/{}.zip".format(
        __version__  # type: ignore # noqa: F821
    ),
    packages=find_packages(exclude=["tests*"]),
    install_requires=list(val.strip() for val in open("requirements.txt")),
    include_package_data=True,
    license="GNU General Public License v3.0",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={"console_scripts": ["boneio=bone.bonecli:cli"]},
)
