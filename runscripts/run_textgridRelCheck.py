#!/usr/bin/env python
# encoding: utf-8

'''configuration file and run script for TextgridReliabilityCheck

@author Bill Bryce (bryce2@illinois.edu)
@updated 2017-03-23

This file doubles as a config file and a run script.
It is intended to be configured by the user in the IDLE Python IDE in lieu
of passing a *.ini configuration file as a command line argument.

'''

###############################################################################
# Modify this line with your working directory.
# Keep the r before the quotes.  It's important.
textgrid_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/data/reliability_check_textgrids"
output_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/output/textgridRelCheck/20170629"

###############################################################################
# If you wish to overwrite all previous output, set overwrite = True;
# otherwise set overwrite = False.
overwrite = False

###############################################################################
# Modify this line with the # of ms of leeway time.
leeway_in_MS = 100

###############################################################################
# Set "report_misslist = True" if you'd like miss locations listed in the report.
# Set "report_misslist = False" if you don't.
report_misslist = False

###############################################################################



# DO NOT MODIFY ANYTHING BELOW THIS LINE
###############################################################################
from mcrp.textgridRelCheck import textgridReliabilityCheck
textgridReliabilityCheck(	textgrid_path, 
							output_path, 
							leeway_in_MS, 
							report_misslist, 
							overwrite,
							)
