import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="motion-detector",
    version="1.0.0",
    author="JP-Ellis",
    author_email="josh@jpellis.me",
    description="Extract motion from CCTV footage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JP-Ellis/extract-motion",
    project_urls={
        "Bug Tracker": "https://github.com/JP-Ellis/extract-motion/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=["opencv-contrib-python", "coloredlogs"],
    entry_points={"console_scripts": ["extract-motion=motion_detector.extract:main"]},
)
