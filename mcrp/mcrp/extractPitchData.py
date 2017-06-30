#!/opt/local/bin/python

import os
from os.path import join
import sys

import cProfile
import codecs
import shutil
import tempfile
import ConfigParser
import math

from praatio.utilities import utils
from praatio import pitch_and_intensity
from utilities.estimate_speech_rate import markupTextgridWithSyllableNuclei
from utilities.removeWavSegments import deleteUnlabeledIntervals
from utilities.padWavs import padEndWithSilence
import utilities.pitchGeneral as general
import utilities.mcrp_io as io


def getPitchData(tgpath, wavpath, outpath, matlabExePath, matlabScriptPath, 
					praatExePath, praatScriptPath):

	"""
	Generates clean textgrid files with the mother's speech isolated from room noise and child speech.
	 
	Directory variables below which are ALL CAPS, such as WAV_DIR and EPOCH_DIR hold files which are
	referenced throughout the workflow as opposed to directories which contain textgrids at a certain
	stage of processing.

	Directories ending in numbers such as textgrids_tier_names_checked_(01) are considered to hold textgrids 
	at certaining milestones of processing, and are placed into the working directory instead of the TEMP
	directory.

	"""

	def _nextStep(n):
		if n == int(n):
			return n+1.0
		else:
			return math.ceil(n)

	# initialize

#	 tg_dir = join(path, "TEXTGRIDS_INTERVALS_MARKED")
	tg_dir = tgpath
#	 WAV_DIR = join(path, "WAVS")
	WAV_DIR = wavpath
	path = outpath
	io.make_dir(path)
	TEMP = tempfile.mkdtemp()
	tgStep = 0.0
	praatStep = 0.0
	uweStep = 0.0
	wavStep = 0.0

	# ensure the tier names are consistent

	tgStep+=0.1
	new_tg_dir = join(path, "_textgrids_{}_tier_names_checked".format(tgStep))

	general.renameTiers(
						tg_dir
						,new_tg_dir
						)

	tg_dir = new_tg_dir

	# replace all labels from Mother tier other than MS

	tgStep+=0.1
	new_tg_dir = join(path, "_textgrids_{}_MS_label_only_in_Mother_tier".format(tgStep))

	general.removeIntervalsFromTierByLabel(
											tg_dir
											,"Mother"
											,"MS"
											,new_tg_dir
											,removeAllBut=True
											)
	tg_dir = new_tg_dir

	# crop portions of intervals in Mother tier overlapping with Mother's Backchannel tier, 
	# meaning that all portions of MS intervals overlapping with LA intervals (laughter) are cropped

	tgStep+=0.1
	new_tg_dir = join(path, "_textgrids_{}_LA_removed".format(tgStep))

	general.isolateMotherSpeech(
								tg_dir
								,"Mother's Backchannel"
								,new_tg_dir
								)

	tg_dir = new_tg_dir

	# set current tg_dir as directory referenced after preprocessing and before cropping

	TG_PREPROCESSED = tg_dir


	# crop portions of intervals in Mother tier overlapping with Child tier, then Room tier, then both.
	# after each cropping, intervals shorter than can be processed are removed from the new Mother tiers
	# non-overlapping portions of intervals in Mother tier are retained

	tgStep = _nextStep(tgStep)
	TG_CS_RMVD_DIR = join(path, "_textgrids_{}_child_removed".format(tgStep))

	tgStep = _nextStep(tgStep)
	TG_ROOM_RMVD_DIR = join(path, "_textgrids_{}_room_removed".format(tgStep))

	tgStep = _nextStep(tgStep)
	TG_CS_ROOM_RMVD_DIR = join(path, "_textgrids_{}_child_room_removed".format(tgStep))

	general.isolateMotherSpeech(
								tg_dir
								,"Child"
								,join(TEMP, "cs_rmvd")
								)
	general.filterShortIntervalsFromTier(
											join(TEMP, "cs_rmvd")
											,"Mother"
											,0.15
											,TG_CS_RMVD_DIR
											)

	general.isolateMotherSpeech(
								tg_dir 
								,"Room"
								,join(TEMP, "rm_rmvd")
								)
	general.filterShortIntervalsFromTier(
											join(TEMP, "rm_rmvd")
											,"Mother"
											,0.15
											,TG_ROOM_RMVD_DIR
											)

	general.isolateMotherSpeech(
								TG_CS_RMVD_DIR
								,"Room"
								,join(TEMP, "cs_rm_rmvd")
								)
	general.filterShortIntervalsFromTier(
											join(TEMP, "cs_rm_rmvd")
											,"Mother"
											,0.15
											,TG_CS_ROOM_RMVD_DIR
											)

################################
# TODO: Delete these lines
################################

#	 TG_CS_ROOM_RMVD_DIR = join(path, "TEXTGRIDS_FROM_OLD_CODE")
#	 TG_CS_RMVD_DIR = join(path, "TEXTGRIDS_OLD_CODE_CS_RMVD")
#	 TG_ROOM_RMVD_DIR = join(path, "TEXTGRIDS_OLD_CODE_ROOM_RMVD")

################################
################################
################################
	tg_dir = TG_CS_ROOM_RMVD_DIR
	

	# create directory of tg_info files (tier entry information as plain text listing)

	TG_INFO_DIR = join(path, "__tg_info")

	general.extractTGInfo(
							tg_dir
							,TG_INFO_DIR
							,"Mother"
							,searchForMothersSpeech=False
							)


	# generate an epoch file (.txt file) corresponding to the Epochs tier in each textgrid (start, stop, label)

	EPOCH_DIR = join(path, "__epochs")

	general.generateEpochFiles(
								tg_dir
								,WAV_DIR
								,EPOCH_DIR
								)

	# pad wav files with about two seconds of silence at the end
	# the next step does not process wav files successfuly if the end of the last MS interval is too near the end of the wav

	wavStep = _nextStep(wavStep)
	new_wav_dir = join(path, "_wavs_{}_padded_w_silence".format(wavStep))

	padEndWithSilence(
						WAV_DIR
						,new_wav_dir
						)

	WAV_DIR = new_wav_dir


	# remove intervals from Mother tier not marked MS
	# this is done in order to try to eliminate loud noises which affect how praat extracts F0 when processing entire wav files

	wavStep = _nextStep(wavStep)
	new_wav_dir = join(path, "_wavs_{}_nonMS_zeroed_out".format(wavStep))

	deleteUnlabeledIntervals(
								tg_dir
								,WAV_DIR
								,"Mother"
								,new_wav_dir
								)

	WAV_DIR = new_wav_dir


	# extract syllable nuclei to determine speech rate (MATLAB REQUIRED)

	wav_temp_dir = join(TEMP, "_subset_wav_files")

	uweStep = _nextStep(uweStep)
	syllable_nuclei_dir = join(path, "_uwe_{}_syllable_nuclei_whole".format(uweStep))

	tgStep = _nextStep(tgStep)
	new_tg_dir = join(path, "_textgrids_{}_syllable_nuclei_added".format(tgStep))

	markupTextgridWithSyllableNuclei(
										WAV_DIR
										,tg_dir
										,"Mother"
										,wav_temp_dir
										,syllable_nuclei_dir
										,matlabExePath
										,matlabScriptPath
										,new_tg_dir
										,printCmd=True
										,outputTGFlag=False
										)
	tg_dir = new_tg_dir


	# acoustic analysis

	uweStep = _nextStep(uweStep)
	nucleus_listing_per_file_dir = join(path, "_uwe_{}_nucleus_listing_mothers_speech".format(uweStep))

	uweStep = _nextStep(uweStep)
	SPEECH_RATE_PER_EPOCH_DIR = join(path, "_uwe_{}_speech_rate_for_epochs".format(uweStep))

	general.aggregateSpeechRate(
								TG_INFO_DIR
								,syllable_nuclei_dir
								,nucleus_listing_per_file_dir
								,44100
								)
	general.uwePhoneCountForEpochs(
									EPOCH_DIR
									,TG_INFO_DIR
									,nucleus_listing_per_file_dir
									,SPEECH_RATE_PER_EPOCH_DIR
									)


	# The following code can be run over the whole audio files, regardless of epoch
	# or textgrids (we'll extract pitch information for the intervals and
	# epochs later) 

	# The first Praat section below extracts pitch data from one wav file with 
	# unlabled intervals silenced.
	#
	# The second Praat section splits labeled intervals into subwavs.
	#
	# It is recommended to use the first section.
	#
	# Regardless of which is used make sure the corresponding aggregate section is 
	# uncommented below, or that both are if both full wavs and subwavs are used.

	praatStep = _nextStep(praatStep)
	praat_dir = join(path, "_praat_{}_75Hz_750Hz_fullwav".format(praatStep))
	utils.makeDir(praat_dir)

	praatStep+=0.1
	PI_FULLWAV_DIR = join(path, "_praat_{}_75Hz_750Hz_fullwav_filter9".format(praatStep))
	utils.makeDir(PI_FULLWAV_DIR)

	for fn in utils.findFiles(WAV_DIR, filterExt=".wav", stripExt=True):
		print(fn+".wav")
		userPitchData = pitch_and_intensity.audioToPI(
														inputPath=WAV_DIR
														,inputFN=fn+".wav"
														,outputPath=praat_dir
														,outputFN=fn+".txt"
														,praatEXE=praatExePath
														,minPitch=75
														,maxPitch=750
														,sampleStep=0.01
														,silenceThreshold=0.03
#														 ,silenceThreshold=0.01
#														 ,silenceThreshold=0.001
#														 ,silenceThreshold=0.0001
#														 ,silenceThreshold=0.00001
														,forceRegenerate=True
#														 ,tgPath=tg_dir
#														 ,tgFN=fn+".TextGrid"
#														 ,tierName="Mother"
#														 ,tmpOutputPath=TEMP
														)
		filteredPitchData = pitch_and_intensity.generatePIMeasures(
																	userPitchData
																	,tg_dir
																	,fn+".TextGrid"
																	,tierName="Epochs"
																	,doPitch=True
																	,medianFilterWindowSize=9
																	)
		with open(join(PI_FULLWAV_DIR, fn+'.txt'), 'w') as outfile:
			for line in filteredPitchData:
				line = [str(x) for x in line]
				outfile.write(",".join(line)+'\n')



#	praatStep = _nextStep(praatStep)
#	praat_dir = join(path, "_praat_{}_75Hz_750Hz_subwav".format(praatStep))
#	utils.makeDir(praat_dir)
#
#	praatStep+=0.1
#	PI_SUBWAV_DIR = join(path, "_praat_{}_75Hz_750Hz_subwav_filter9".format(praatStep))
#	utils.makeDir(PI_SUBWAV_DIR)
#
#	for fn in utils.findFiles(WAV_DIR, filterExt=".wav", stripExt=True):
#		print(fn+".wav")
#		userPitchData = pitch_and_intensity.audioToPI(
#														inputPath=WAV_DIR
#														,inputFN=fn+".wav"
#														,outputPath=praat_dir
#														,outputFN=fn+".txt"
#														,praatEXE=praatExePath
#														,minPitch=75
#														,maxPitch=750
#														,sampleStep=0.01
#														,silenceThreshold=0.03
##														 ,silenceThreshold=0.01
##														 ,silenceThreshold=0.001
##														 ,silenceThreshold=0.0001
##														 ,silenceThreshold=0.00001
#														,forceRegenerate=True
#														,tgPath=tg_dir
#														,tgFN=fn+".TextGrid"
#														,tierName="Mother"
#														,tmpOutputPath=TEMP
#														)
#		filteredPitchData = pitch_and_intensity.generatePIMeasures(
#																	userPitchData
#																	,tg_dir
#																	,fn+".TextGrid"
#																	,tierName="Epochs"
#																	,doPitch=True
#																	,medianFilterWindowSize=9
#																	)
#		with open(join(PI_SUBWAV_DIR, fn+'.txt'), 'w') as outfile:
#			for line in filteredPitchData:
#				line = [str(x) for x in line]
#				outfile.write(",".join(line)+'\n')



	EVENT_DIR = join(path, "__event_frequency_and_duration")
	general.eventStructurePerEpoch(
									EPOCH_DIR
									,TG_CS_ROOM_RMVD_DIR
									,TG_CS_RMVD_DIR
									,TG_ROOM_RMVD_DIR
									,TG_PREPROCESSED
									,EVENT_DIR
									,"Mother"
									,"Mother's Backchannel"
									)


	# TODO: generalize this so that 'P' is not output for every type of session
	EPOCH_ROW_HEADER_DIR = join(path, "__epoch_row_header")
	general.generateEpochRowHeader(
									EPOCH_DIR
									,EPOCH_ROW_HEADER_DIR
									,"P"
									)

	headerStr = ("file,id,session,interval,int_start,int_end,int_dur,"
				 "ms_dur_s,ms_freq,ms_child_speech_filtered_dur_s,"
				 "ms_noise_filtered_dur_s,ms_full_dur_s,lost_ms_dur_s,"
				 "fp_dur_s,fp_freq,la_dur_s,la_freq,"
				 "uwe_sylcnt,f0_mean,"
				 "f0_max,f0_min,f0_range,f0_var,f0_std"
				 )

	general.aggregateFeatures(
								path
								,[
									os.path.split(EPOCH_ROW_HEADER_DIR)[1]
									,os.path.split(EVENT_DIR)[1]
									,os.path.split(SPEECH_RATE_PER_EPOCH_DIR)[1]
									,os.path.split(PI_FULLWAV_DIR)[1]
								]
								,"__aggr_fullwav"
								,headerStr
								)

#	general.aggregateFeatures(
#								path
#								,[
#									os.path.split(EPOCH_ROW_HEADER_DIR)[1]
#									,os.path.split(EVENT_DIR)[1]
#									,os.path.split(SPEECH_RATE_PER_EPOCH_DIR)[1]
#									,os.path.split(PI_SUBWAV_DIR)[1]
#								]
#								,"__aggr_subwav"
#								,headerStr
#								)

	# remove the temp directory			   
	shutil.rmtree(TEMP)

