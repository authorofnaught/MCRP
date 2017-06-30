'''
Created on Jul 27, 2015

@author: tmahrt

Two examples of how to use uwe_sr with two different types of data and
two different tasks.

First, it is possible to run this data on either whole files or on segments
of a file (here the segment times are extracted from a textgrid but you could
use other input sources).

Second, in one task, the syllable nuclei are seralized in a textgrid.  In the
other task, the speech rate is calculated.
'''

from os.path import join

from praatio import tgio
from praatio import praatio_scripts

from pyacoustics.signals import audio_scripts
from pyacoustics.speech_rate import uwe_sr
from pyacoustics.utilities import utils
from pyacoustics.utilities import my_math


def _runSpeechRateEstimate(wavPath, syllableNucleiPath, matlabEXE,
                           matlabScriptsPath, printCmd=True):
    uwe_sr.findSyllableNuclei(wavPath, syllableNucleiPath, matlabEXE,
                              matlabScriptsPath, printCmd)
    
    
def _runSpeechRateEstimateOnIntervals(wavPath, tgPath, tierName, wavTmpPath,
                                      syllableNucleiPath, matlabEXE,
                                      matlabScriptsPath, printCmd=True,
                                      outputTGFlag=False):
    
    utils.makeDir(wavTmpPath)
    # Split audio files into subsections based on textgrid intervals
    for name in utils.findFiles(wavPath, filterExt=".wav", stripExt=True):
        print("\tsplitting {}".format(name))
        praatio_scripts.splitAudioOnTier(join(wavPath, name + ".wav"),
                                         join(tgPath, name + ".TextGrid"),
                                         tierName, wavTmpPath, outputTGFlag)
        
    uwe_sr.findSyllableNuclei(wavTmpPath, syllableNucleiPath, matlabEXE,
                              matlabScriptsPath, printCmd)



def _addSyllableNucleiToTextgrids(wavPath, tgPath, tierName,
                                 syllableNucleiPath, outputPath):
    # Add syllable nuclei to textgrids
    for name in utils.findFiles(wavPath, filterExt=".wav", stripExt=True):
        
        tg = tgio.openTextGrid(join(tgPath, name + ".TextGrid"))
        entryList = tg.tierDict[tierName].entryList
        startTimeList = [entry[0] for entry in entryList]
        nucleusSyllableList = uwe_sr.toAbsoluteTime(name, syllableNucleiPath,
                                                    startTimeList)
######### DEBUG  ############
        for i in range(len(startTimeList)):
            print("{}: {}".format(startTimeList[i], len(nucleusSyllableList[i])))
#        print("startTimeList has {} entries:\n{}".format(len(startTimeList), startTimeList))
#        print("nucleusSyllableList has {} sublists:\n{}".format(len(nucleusSyllableList), nucleusSyllableList))
#############################
        flattenedSyllableList = [nuclei for sublist in nucleusSyllableList
                                 for nuclei in sublist]
        wavFN = join(wavPath, name + ".wav")
        duration = audio_scripts.getSoundFileDuration(wavFN)
        
        oom = my_math.orderOfMagnitude(len(flattenedSyllableList))
        labelTemplate = "%%0%dd" % (oom + 1)

        entryList = [(timestamp, labelTemplate % i)
                     for i, timestamp in enumerate(flattenedSyllableList)]
#        print flattenedSyllableList
        tier = tgio.PointTier("Syllable Nuclei", entryList, 0, duration)
        
        tgFN = join(tgPath, name + ".TextGrid")
        tg = tgio.openTextGrid(tgFN)
        tg.addTier(tier)
        tg.save(join(outputPath, name + ".TextGrid"))
        

def _calculateSyllablesPerSecond(wavPath, syllableNucleiPath):
        
    for name in utils.findFiles(wavPath, filterExt=".wav", stripExt=True):
        nucleusSyllableList = uwe_sr.toAbsoluteTime(name, syllableNucleiPath,
                                                    [0, ])
        nucleusSyllableList = [nucleus for subList in nucleusSyllableList
                               for nucleus in subList]
        numSyllables = len(nucleusSyllableList)
        wavFN = join(wavPath, name + ".wav")
        duration = audio_scripts.getSoundFileDuration(wavFN)
        
        print("%s - %.02f syllables/second" %
              (name, numSyllables / float(duration)))
        

def _calculateSyllablesPerSecondForIntervals(wavPath, tgPath, tierName,
                                             syllableNucleiPath):
    # Add syllable nuclei to textgrids
    for name in utils.findFiles(wavPath, filterExt=".wav", stripExt=True):
        
        tg = tgio.openTextGrid(join(tgPath, name + ".TextGrid"))
        entryList = tg.tierDict[tierName].entryList
        startTimeList = [entry[0] for entry in entryList]
        nucleusSyllableList = uwe_sr.toAbsoluteTime(name, syllableNucleiPath,
                                                    startTimeList)
        
        durationList = []
        for intervalList, entry in utils.safeZip([nucleusSyllableList,
                                                  entryList],
                                                 enforceLength=True):
            start, stop = entry[0], entry[1]
            duration = len(intervalList) / (stop - start)
            durationList.append(str(duration))
        
        print("%s - %s (syllables/second for each interval)" %
              (name, ",".join(durationList)))
            

def markupTextgridWithSyllableNuclei(wavPath, tgPath, tierName, wavTmpPath,
                                     syllableNucleiPath, matlabEXE,
                                     matlabScriptsPath, outputPath,
                                     printCmd=True, outputTGFlag=False):
    
    utils.makeDir(outputPath)
    
    # This can be commented out and instead, you can run the code directly
    # from matlab, then you can start directly from the next line
    print("RUN_SPEECH_RATE_ESTIMATE_ON_INTERVALS")  #TODO DEBUG
    _runSpeechRateEstimateOnIntervals(wavPath, tgPath, tierName, wavTmpPath,
                                      syllableNucleiPath, matlabEXE,
                                      matlabScriptsPath, printCmd,
                                      outputTGFlag)
    print("ADD_SYLLABLE_NUCLEI_TO_TEXTGRIDS")       #TODO DEBUG
    _addSyllableNucleiToTextgrids(wavPath, tgPath, tierName,
                                  syllableNucleiPath, outputPath)
    print("CALCULATE_SYLLABLES_PER_SECOND_FOR_INTERVALS")   #TODO DEBUG
    _calculateSyllablesPerSecondForIntervals(wavPath, tgPath, tierName,
                                             syllableNucleiPath)


def getSpeechRateForIntervals(wavPath, syllableNucleiPath, matlabEXE,
                              matlabScriptsPath, printCmd=True):

    # This can be commented out and instead, you can run the code directly
    # from matlab, then you can start directly from the next line
    _runSpeechRateEstimate(wavPath, syllableNucleiPath, matlabEXE,
                           matlabScriptsPath, printCmd)
    
    _calculateSyllablesPerSecond(wavPath, syllableNucleiPath)


if __name__ == "__main__":
    
    _rootDir = "/Users/authorofnaught/Desktop/MP_CODE_TESTING/"
    _wavPath = join(_rootDir, "wavs")
    _syllableNucleiPath = join(_rootDir, "syllableNuclei_portions")
    _matlabEXE = "/Applications/MATLAB_R2015a.app/bin/matlab"
    _matlabScriptsPath = ("/Users/authorofnaught/pyAcoustics/matlabScripts")
    
#     getSpeechRateForIntervals(_wavPath, _syllableNucleiPath, _matlabEXE,
#                               _matlabScriptsPath)

    _wavTmpPath = join(_rootDir, "subset_wav_files")
    _tgPath = join(_rootDir, "textgrids_intervals_marked")
    _tierName = "Mother"
    _syllableNucleiPath = join(_rootDir, "syllableNuclei_whole")
    _outputPath = join(_rootDir, "textgrids_w_syllable_nucleus_markings")
    
    markupTextgridWithSyllableNuclei(_wavPath, _tgPath, _tierName, _wavTmpPath,
                                     _syllableNucleiPath, _matlabEXE,
                                     _matlabScriptsPath, _outputPath)

