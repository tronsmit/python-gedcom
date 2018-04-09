from distutils.core import setup

setup(
    name='python-gedcom',
    version='1.0.0dev',
    packages=['gedcom', ],
    license='GPLv2',
    package_dir={'': '.'},
    description=open('README.md').readlines()[0].strip(),
    long_description=open('README.md').read(),
    maintainer='Nicklas Reincke',
    maintainer_email='contact@reynke.com',
    url='https://github.com/nickreynke/python-gedcom',
)
