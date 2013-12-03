from setuptools import setup
from setuptools.command.test import test as TestCommand
import os
import sys

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        # import here, because outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

with open('requirements.txt') as f:
    required = [req for req in f.read().splitlines()
                if req and not req.startswith("git+https")]

setup(
    name="seamless_karma",
    version="0.0.1",
    author="David Baumgold",
    author_email="david@davidbaumgold.com",
    url="http://www.seamlesskarma.com",
    description="track and manage your Seamless.com corporate allocations",
    license="MIT",
    install_requires=required,
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    zip_safe=False,
)