"""Python setup.py for finance package"""
import io
import os
from setuptools import find_packages, setup


def read(*paths, **kwargs):
    """Read the contents of a text file safely.
    >>> read("finance", "VERSION")
    '0.1.0'
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path):
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


setup(
    name="finance",
    version=read("finance", "VERSION"),
    description="Awesome finance created by sergioUjo",
    url="https://github.com/sergioUjo/finance/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="sergioUjo",
    packages=find_packages(exclude=["tests", ".github"]),
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": ["finance = finance.__main__:main"]
    },
    extras_require={"test": read_requirements("requirements-test.txt")},
)
