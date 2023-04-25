from setuptools import find_packages, setup

setup(
    name="roster-ctl",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=0.27.4",
        "langchain==0.0.142",
        "pytest==7.3.1",
        "black==23.3.0",
        "tiktoken==0.3.3",
        "llama-index==0.5.22",
    ],
    entry_points={"console_scripts": ["roster-ctl = roster_ctl:main"]},
)
