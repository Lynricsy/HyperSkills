from setuptools import find_packages, setup

setup(
    name="csvkit-lite",
    version="0.4.2",
    description="Small helpers for reading and reshaping CSV files",
    packages=find_packages(exclude=["tests"]),
    install_requires=["chardet>=5", "python-dateutil>=2.8"],
    extras_require={"dev": ["black==23.1.0", "flake8==6.0.0", "isort", "pytest"]},
    python_requires=">=3.9",
)
