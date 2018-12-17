import os
from setuptools import find_packages, setup

def readfile(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

README = readfile('README.rst')
VERSION = readfile('VERSION')

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='isdc-drought',
    version=VERSION,
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',  # temporary license
    description='Process and display drought data.',
    long_description=README,
    url='https://www.example.com/',
    author='ASDC Dev',
    author_email='yourname@example.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',  
        'License :: OSI Approved :: BSD License',  # temporary license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
