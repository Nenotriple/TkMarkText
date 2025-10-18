from setuptools import setup, find_packages
from pathlib import Path

readme = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name='tkmarktext',
    version='1.00',
    author='Nenotriple',
    url='https://github.com/Nenotriple/tkmarktext',
    description='Embeddable text panel and popup window with markdown-style formatting.',
    long_description=readme,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.10",
)
