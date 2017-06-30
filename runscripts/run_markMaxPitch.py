#!/usr/bin/env python
# encoding: utf-8

'''configuration file and run script for MarkMaxPitch

@author Bill Bryce (bryce2@illinois.edu)
@updated 2017-04-01

This file doubles as a config file and a run script.
It is intended to be configured by the user in the IDLE Python IDE in lieu
of passing a *.ini configuration file as a command line argument.

'''

###############################################################################
# Modify the textgrid, wav, and output directories.
# Keep the r before the quotes.  It's important.
textgrid_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/output/extractPitchData/play/_textgrids_3.0_child_room_removed"
wav_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/data/working/play/wav"
output_path = r"/Users/authorofnaught/Projects/Maternal_Prosody/output/markMaxPitch/play"

###############################################################################
# If you wish to overwrite all previous output, set overwrite = True;
# otherwise set overwrite = False.
overwrite = False

###############################################################################
# Modify to the location fo Praat on your machine.
praat_path = r"/Applications/Praat.App/Contents/MacOS/Praat"

###############################################################################
# Modify the name of the textgrid tier to be considered.
tier_name = "Mother"

###############################################################################
# Modify the pitch range that Praat should use.
min_pitch_value = 75
max_pitch_value = 750

###############################################################################
# Modify the number of intervals to consider; for example, if this parameter is
# set to 30, then only the intervals with the top 30 pitch values will be 
# output.
number_of_intervals_to_output = 30

###############################################################################
# Modify the number of intervals per tier; for example, if this number is set 
# to 10, and the script will output the top 30 intervals, there will be 3 tiers
# in the output textgrid with 10 intervals in each tier.
number_of_intervals_per_tier = 10

###############################################################################



# DO NOT MODIFY ANYTHING BELOW THIS LINE
###############################################################################
from mcrp.markMaxPitch import markMaxPitchInDir
markMaxPitchInDir(	textgrid_path, 
					wav_path,
					output_path,
					tier_name, 
					min_pitch_value, 
					max_pitch_value,
					number_of_intervals_to_output, 
					number_of_intervals_per_tier, 
					praat_path,
					overwrite,
					)
