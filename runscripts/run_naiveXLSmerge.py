#!/usr/bin/env python
# encoding: utf-8

'''configuration file and run script for NaiveXLSMerge

@author Bill Bryce (bryce2@illinois.edu)
@updated 2017-03-23

This file doubles as a config file and a run script.
It is intended to be configured by the user in the IDLE Python IDE in lieu
of passing a *.ini configuration file as a command line argument.

'''

###############################################################################
# Modify this line with your working directory.
# Keep the r before the quotes.  It's important.
input_dir_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/data/naiveXLSmerge/sample"
output_dir_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/output/naiveXLSmerge/20170629"

###############################################################################



# DO NOT MODIFY ANYTHING BELOW THIS LINE
###############################################################################
from mcrp.naiveXLSmerge import merge
merge(input_dir_path, output_dir_path)
