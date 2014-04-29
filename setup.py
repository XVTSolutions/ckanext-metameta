from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(
    name='ckanext-metameta',
    version=version,
    description="metadata",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Mitsuhiro Ozaki',
    author_email='mitsuhiro@xvt.com.au',
    url='',
    license='XVT Solutions',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        # Add plugins here, e.g.
        metameta=ckanext.metameta.plugin:MetametaPlugin
        
        [paste.paster_command]
        clean=ckanext.metameta.commands.clean:CleanCommand
    ''',
)
