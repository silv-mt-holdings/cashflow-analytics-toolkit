from setuptools import setup, find_packages

setup(
    name="cashflow-analytics-toolkit",
    version="1.0.0",
    author="Silv MT Holdings",
    description="Cash flow analytics toolkit - Analyzes trends, volatility, NSF, ADB, and banking behavior metrics",
    url="https://github.com/silv-mt-holdings/cashflow-analytics-toolkit",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.8",
    install_requires=[
        "transaction-classifier-toolkit @ git+https://github.com/silv-mt-holdings/transaction-classifier-toolkit.git",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
    ],
    extras_require={"dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0"]},
)
