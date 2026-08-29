from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirement.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="space-map",
    version="0.2.0",
    packages=find_packages(exclude=['tests', 'tests.*', 'examples', 'docs']),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'space-map=space_map.api.cli:main',
        ],
    },
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.9',
            'ipykernel>=6.0',
            'nbclient>=0.6',
        ],
        'docs': [
            'mkdocs>=1.2',
            'mkdocs-material>=8.0',
            'mkdocstrings>=0.18',
            'mkdocstrings-python>=0.6',
            'mkdocs-git-revision-date-localized-plugin>=1.0',
        ],
    },
    description="Reconstructing atlas-level single-cell 3D tissue maps from serial sections",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rongduo Han, Chenchen Zhu, Cihan Ruan",
    author_email="czhu5@stanford.edu",
    url="https://github.com/czhu/space-map",
    project_urls={
        "Bug Reports": "https://github.com/czhu/space-map/issues",
        "Documentation": "https://czhu.github.io/space-map",
        "Source": "https://github.com/czhu/space-map",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    keywords="spatial-transcriptomics 3d-reconstruction tissue-mapping image-registration lddmm codex xenium",
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)
