#!/usr/bin/env python
from setuptools import setup, find_packages


dev_requires = [
    'Sphinx==1.2.2',
]

tests_requires = [
    'factory_boy==2.4.1',
    'mock==1.0.1',
]

install_requires = [
    'nodeconductor>=0.110.0',
    'python-digitalocean>=1.5',
]


setup(
    name='nodeconductor-digitalocean',
    version='0.1.0.dev0',
    author='OpenNode Team',
    author_email='info@opennodecloud.com',
    url='http://nodeconductor.com',
    description='NodeConductor plugin for managing DigitalOcean resources.',
    long_description=open('README.rst').read(),
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
    install_requires=install_requires,
    zip_safe=False,
    extras_require={
        'test': tests_requires,
        'dev': dev_requires,
    },
    entry_points={
        'nodeconductor_extensions': (
            'nodeconductor_digitalocean = nodeconductor_digitalocean.extension:DigitalOceanExtension',
        ),
    },
    tests_require=tests_requires,
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT',
        'Operating System :: OS Independent',
    ],
)