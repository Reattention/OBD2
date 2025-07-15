from setuptools import setup, find_packages

setup(
    name="bmw-obd2-diagnostics",
    version="0.1.0",
    description="BMW OBD2 Diagnostics Tool with Real ECU Communication",
    author="BMW OBD2 Team",
    packages=find_packages(),
    install_requires=[
        "obd>=0.7.1",
        "pyserial>=3.4",
        "bluetooth-adapters>=0.15.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)