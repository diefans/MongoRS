"""package setup"""

import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    """Our test runner."""

    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ["tests"]

    def finalize_options(self):
        # pylint: disable=W0201
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name="MongoRS",
    version="0.0.1",

    package_dir={'': 'src'},
    namespace_packages=[],
    packages=find_packages(
        'src',
        exclude=[]
    ),
    entry_points={
        "console_scripts": [
            "mongors = mongors.scripts:cli"
        ]
    },

    install_requires=[
        "pymongo",
        "click",
        "gevent",
        "simplejson",
    ],

    cmdclass={'test': PyTest},
    tests_require=[
        # tests
        'pytest',
        'pytest-pep8',
    ]
)
