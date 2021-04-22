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

from setuptools import setup
from setuptools import find_packages

setup(
    name='pip_services3_mongodb',
    version='3.0.6',
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
        'iso8601', 'PyYAML', 'pymongo', 'pip_services3_commons', 'pip_services3_components', 'pip_services3_data'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]    
)
