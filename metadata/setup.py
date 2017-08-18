from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))


with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(here, "VERSION"), encoding="utf-8") as f:
    version = f.read().strip()

with open(path.join(here, "requirements.txt")) as f:
    requirements = f.read().split('\n')

setup(
    name='serene_metadata',
    version=version,
    description='Serene Metadata',
    long_description=long_description,
    author='',
    author_email='',
    url='http://',
    license="Apache-2.0",
    scripts=[
    ],
    packages=find_packages(exclude=['tests']),
    # Define entry points to your program
    # "command=package:function"
    entry_points={
        'console_scripts': [
            'serene_metadata=serene_metadata.main:main',
        ]
    },
    test_suite='nose.collector',
    tests_require=['nosexcover'],
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers, Data Scientists",
        "Topic :: Software :: Graph Analysis",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
    ],
    keywords="Graph Analysis, Solr, Schema, Ontology, ETL",

    # Requirements for specific build cycles go here
    # { 'build': [requirements,for,build] }
    extras_require={},

    # For data files within your package
    # { package_name: [filenames, in, the, package] }
    package_data={
    },

    # For data files outside your package
    # [ ( directory, [filenames, in, the, directory] }
    data_files=[],

)
