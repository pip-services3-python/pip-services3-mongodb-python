"""
Pip.Services Mongodb
------------------

Pip.Services is an open-source library of basic microservices.
pip_services3_mongodb provides MongoDb persistence components.

Links
`````

* `website <http://github.com/pip-services/pip-services>`_
* `development version <http://github.com/pip-services3-python/pip-services3-mongodb-python>`

"""

try:
    readme = open('readme.md').read()
except:
    readme = __doc__

from setuptools import find_packages
from setuptools import setup

setup(
    name='pip_services3_mongodb',
    version='3.2.5',
    url='http://github.com/pip-services3-python/pip-services3-mongodb-python',
    license='MIT',
    author='Conceptual Vision Consulting LLC',
    author_email='seroukhov@gmail.com',
    description='MongoDb persistence components for Pip.Services in Python',
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=['config', 'data', 'test']),
    include_package_data=True,
    zip_safe=True,
    platforms='any',
    install_requires=[
        'pymongo >= 4.0.1, < 5.0.0',

        'pip_services3_commons >= 3.3.10, < 4.0',
        'pip_services3_components >= 3.5.4, < 4.0',
        'pip_services3_data >= 3.2.3, < 4.0'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]    
)
