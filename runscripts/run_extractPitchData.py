#!/usr/bin/env python
# encoding: utf-8

'''configuration file and run script for extractPitchData

@author Bill Bryce (bryce2@illinois.edu)
@updated 2017-03-23

This file doubles as a config file and a run script.
It is intended to be configured by the user in the IDLE Python IDE in lieu
of passing a *.ini configuration file as a command line argument.

'''

###############################################################################
# Modify this section with your working directories.
# Keep the r before the quotes.  It's important.
textgrid_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/data/working/play/textgrid"
wav_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/data/working/play/wav"
output_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/output/extractPitchData/20170625/play"

###############################################################################
# If you wish to overwrite all previous output, set overwrite = True;
# otherwise set overwrite = False.
#overwrite = False
# TODO: set up better overwriting option in extractPitchData.py

###############################################################################
# Specify the location of your matlab application and the matlab scripts
matlab_exe_path = "/Applications/MATLAB_R2015a.app/bin/matlab"
matlab_script_path = "/Users/authorofnaught/Projects/Maternal_Prosody/mcrp/mcrp/matlabScripts/"

###############################################################################
# Specify the location of your matlab application and the matlab scripts
praat_exe_path = "/Applications/Praat.app/Contents/MacOS/Praat"
praat_script_path = "/Users/authorofnaught/Projects/Maternal_Prosody/mcrp/mcrp/praatScripts/"

###############################################################################



# DO NOT MODIFY ANYTHING BELOW THIS LINE
###############################################################################
from mcrp.extractPitchData import getPitchData
getPitchData(	textgrid_path, 
				wav_path,
				output_path,
				matlab_exe_path,
				matlab_script_path,
				praat_exe_path,
				praat_script_path,
#				overwrite,
				)
