'''
Created on Oct 4, 2016

@author: Tim Mahrt (tmahrt)

Modifed March 26, 2017 by Bill Bryce (authorofnaught):

Script now provided to process directories, and the number of 
intervals in output textgrids may now be specified by user.

'''

import sys
import os
from os.path import join

import wave

from praatio import tgio
from praatio import pitch_and_intensity
from praatio import praatio_scripts
import utilities.mcrp_io as io

def _getSoundFileDuration(fn):
	'''
	Returns the duration of a wav file (in seconds)

	'''
	audiofile = wave.open(fn, "r")
	
	params = audiofile.getparams()
	framerate = params[2]
	nframes = params[3]
	
	duration = float(nframes) / framerate
	return duration
		

def deleteUnlabeledIntervals(tgFN, wavFN, tierName, outputFN):
	'''
	Removes all audio from sections of wav file not inside labeled intervals

	'''

	tg = tgio.openTextGrid(tgFN)
	
	# Get the unlabeled intervals
	tier = tg.tierDict[tierName].fillInBlanks()
	entryList = [entry for entry in tier.entryList
				 if entry[2] == ""]
	
	# Sometimes the textgrid and wav file differ by some small amount
	# If the textgrid is longer, the script crashes
	wavDur = _getSoundFileDuration(wavFN)
	if entryList[-1][1] > wavDur and entryList[-1][0] < wavDur:
		entryList[-1] = (entryList[-1][0], wavDur, "")

	try:
		praatio_scripts.deleteWavSections(wavFN, outputFN, entryList,
									  doShrink=False)
	except wave.Error:
		print("There was a problem processing {}".format(os.path.basename(tgFN)))


def markMaxPitch(tgFNFullPath, wavFNFullPath, outputPath, tierName, minPitch, maxPitch,
				 numTopPitchIntervals, numIntervalsPerTier, praatEXE):
	'''
	Returns a textgrid whose tier intervals denote locations of highest pitch 
	measurements in the wav file it annotates.

	'''


	tgFN = os.path.basename(tgFNFullPath)	
	wavFN = os.path.basename(wavFNFullPath)

	print("Processing max pitch from {}".format(wavFN))

	io.make_dir(outputPath)
	
	cleanedWavPath = join(outputPath, "cleanedWavs")
	io.make_dir(cleanedWavPath)	
	cleanedWavFN = join(cleanedWavPath, wavFN)
	
	pitchPath = join(outputPath, "pitch")
	io.make_dir(pitchPath)
	pitchFN = io.get_filename_w_new_ext(wavFN, "pitch")

	textgridPath = join(outputPath, "textgrid")
	io.make_dir(textgridPath)
	textgridFN = join(textgridPath, tgFN)

	
	# 1 Delete unlabeled segments
	if not os.path.exists(cleanedWavFN):
		deleteUnlabeledIntervals(tgFNFullPath, wavFNFullPath,
								 tierName, cleanedWavFN)
	
	# 2 Measure pitch from 'pruned' recording file 
	piList = pitch_and_intensity.audioToPI(cleanedWavPath, wavFNFullPath, pitchPath,
										   pitchFN,
										   praatEXE, minPitch, maxPitch,
										   forceRegenerate=False)

	# 3 Get pitch from each interval
	tg = tgio.openTextGrid(tgFNFullPath)
	tier = tg.tierDict[tierName]
	piListSegmented = tier.getValuesInIntervals(piList)

	# 4 Get max pitch from each interval
	entryList = []
	for interval, dataList in piListSegmented:
		pitchList = [f0Val for _, f0Val, _ in dataList]
		if len(pitchList) == 0:
			continue
		maxF0Val = max(pitchList)
		entryList.append((interval[0], interval[1], maxF0Val))
	
	entryList.sort(key=lambda x: x[2], reverse=True)
	entryList = [(start, stop, str(label)) for start, stop, label in entryList]
	
	# 5 Report the top intervals
	outputTG = tgio.Textgrid()
	for i in xrange(0, numTopPitchIntervals, numIntervalsPerTier):
		name = "top %d" % (i + 10)
		subEntryList = entryList[i:i + 10]
		minT = tg.minTimestamp
		maxT = tg.maxTimestamp
		
		tier = tgio.IntervalTier(name, subEntryList, minT, maxT)
		outputTG.addTier(tier)
		
	outputTG.save(textgridFN)


def markMaxPitchInDir(tgpath, wavpath, outdirpath, tierName, minPitch, maxPitch, 
						numTopPitchIntervals, numIntervalsPerTier, praatEXE, overwrite):
	'''
	Calls markMaxPitch for each file in a directory.

	'''

	io.make_dir(outdirpath, overwrite)

	tgFiles = io.get_files_w_ext(tgpath, "TextGrid")
	wavFiles = io.get_files_w_ext(wavpath, "wav")

	for tgfn in tgFiles:
		path, fn = os.path.split(tgfn)
		wavfn = io.get_filename_w_new_ext(fn, "wav")
		wavfn = os.path.join(wavpath, wavfn)
		if os.path.exists(wavfn):
			markMaxPitch(tgfn, wavfn, outdirpath, tierName, minPitch, maxPitch, 
							numTopPitchIntervals, numIntervalsPerTier, praatEXE)
		else:
			sys.stderr.write("No corresponding wav file for {}\n".format(tgfn))
