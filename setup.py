from setuptools import find_packages, setup

setup(
    name="pyramidi",
    version="0.0.1",
    author="Konrad Swierczek",
    author_email="swierckj@mcmaster.ca",
    description="A package for processing, manipulating, and analyzing MIDI files using Mido.",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.10.12",
    install_requires=["mido==1.3.2", "pandas==2.0.0", "scipy==1.10.1"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL3",
        "Operating System :: OS Independent",
    ],
    url="https://github.com/konradswierczek/pyramidi",
    project_urls={
        "Homepage": "https://github.com/konradswierczek/pyramidi",
        "Issues": "https://github.com/konradswierczek/pyramidi/issues",
    },
    packages=find_packages(),
)
