from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="autopost-bot",
    version="1.0.0",
    author="dyukk-y",
    description="Advanced Python bot for automatic content publishing with timezone support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dyukk-y/lilililililili",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "autopost-bot=bot:AutoPostBot",
        ],
    },
    keywords="autopost bot posting scheduler timezone telegram vk instagram twitter",
    project_urls={
        "Bug Reports": "https://github.com/dyukk-y/lilililililili/issues",
        "Documentation": "https://github.com/dyukk-y/lilililililili#readme",
        "Source Code": "https://github.com/dyukk-y/lilililililili",
    },
    zip_safe=False,
)
