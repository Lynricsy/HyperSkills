from setuptools import find_packages, setup

setup(
    name="acme-reporting",
    version="0.4.2",
    description="Internal reporting helpers",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "requests==2.31.0",
        "click>=8.0",
        "pyyaml",
    ],
    entry_points={"console_scripts": ["acme-report=acme_reporting.cli:main"]},
    python_requires=">=3.9",
)
