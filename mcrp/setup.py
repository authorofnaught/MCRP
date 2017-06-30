#!/usr/bin/env python
# encoding: utf-8

'''
Package created by Bill Bryce
Last update: 2017-04-01

'''

from setuptools import setup, find_packages

setup(
	name="mcrp",
	version="1.0",
	description="Various scripts for MCRP project.",
	url="http://github.com/authorofnaught/mcrp",
	author="Bill Bryce",
	author_email="authorofnaught@gmail.com",
	license="LICENSE",
#	packages=["mcrp"],
	packages = find_packages(),
	zip_safe=False
)
