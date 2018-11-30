from setuptools import setup

setup(
    name='python-gedcom',
    version='0.2.4dev',
    packages=['gedcom', ],
    license='GPLv2',
    package_dir={'': '.'},
    description='A Python module for parsing, analyzing, and manipulating GEDCOM files.',
    long_description=open('README.md').read(),
    maintainer='Nicklas Reincke',
    maintainer_email='contact@reynke.com',
    url='https://github.com/nickreynke/python-gedcom',
)
