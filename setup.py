"""
Setup configuration for AshborneSDK
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

setup(
    name="ashborne-sdk",
    version="1.0.0",
    author="Ashborne Method",
    author_email="contact@ashbornemethod.com",
    description="Modular AI Governance and Licensing SDK",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ashbornemethod/AshborneSDK_v1",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ashborne-sdk=main:app",
            "ashborne-builder=builder_pi:main",
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai governance licensing sdk fastapi",
    project_urls={
        "Bug Reports": "https://github.com/ashbornemethod/AshborneSDK_v1/issues",
        "Source": "https://github.com/ashbornemethod/AshborneSDK_v1",
        "Documentation": "https://github.com/ashbornemethod/AshborneSDK_v1#readme",
    },
)
