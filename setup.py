import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ct600",
    version="1.0.0",
    author="Cybermaggedon",
    author_email="mark@cyberapocalypse.co.uk",
    description="UK HMRC Corporation Tax submission",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cybermaggedon/ct600",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    download_url = "https://github.com/cybermaggedon/ct600/archive/refs/tags/v1.0.0.tar.gz",
    install_requires=[
        'aiohttp',
        'py-dmidecode',
        'requests',
        'ixbrl-parse'
    ],
    scripts=[
        "scripts/ct600",
        "scripts/corptax-test-service"
    ]
)

