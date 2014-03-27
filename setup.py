#!/usr/bin/env python
# coding=utf-8
from __future__ import unicode_literals

from setuptools import setup
from setuptools.command.test import test as TestCommand
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


def extract_requirements(f):
    return [
        req for req in f.read().splitlines()
        if not req.startswith("-r") and not req.startswith("#")
        and not req.startswith("git+")
    ]


setup(
    name="seamless_karma",
    version="0.0.1",
    author="David Baumgold",
    author_email="david@davidbaumgold.com",
    url="http://www.seamlesskarma.com",
    description="track and manage your Seamless.com corporate allocations",
    license="MIT",
    install_requires=extract_requirements(open('requirements.txt')),
    tests_require=extract_requirements(open('dev-requirements.txt')),
    cmdclass={'test': PyTest},
    zip_safe=False,
)
