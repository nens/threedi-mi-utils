from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="threedi-mi-utils",
    version="0.1.0",
    packages=find_packages(),
    url="https://github.com/nens/threedi-mi-utils",
    license="GNU General Public License v3.0",
    author="Łukasz Dębek",
    description="Python package with tools for managing the working 3Di directory structure",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
