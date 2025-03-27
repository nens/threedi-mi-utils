from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="threedi-mi-utils",
    version="0.1.8",
    packages=find_packages(),
    url="https://github.com/nens/threedi-mi-utils",
    license="GNU General Public License v3.0",
    author="Łukasz Dębek",
    description="Python package with utilities for the 3Di Modeller Interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "threedi-schema==0.*"
    ]
)
