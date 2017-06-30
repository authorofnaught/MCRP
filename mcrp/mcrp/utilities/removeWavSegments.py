'''
Created on Sep 7, 2016

@author: Tim
'''

from os.path import join
import wave

from praatio import tgio
from praatio import praatio_scripts
from praatio.utilities import utils


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
        

def deleteUnlabeledIntervals(tgPath, wavPath, tierName, outputPath):
    """
    Does not assume TextGrid and wav files are inside same directory
    """    

    utils.makeDir(outputPath)
    
    for name in utils.findFiles(tgPath,
                                filterExt=".TextGrid",
                                stripExt=True):
        
        tg = tgio.openTextGrid(join(tgPath, name + ".TextGrid"))
        
        # Get the unlabeled intervals
        tier = tg.tierDict[tierName].fillInBlanks()
        entryList = [entry for entry in tier.entryList
                     if entry[2] == ""]
        
        wavFN = join(wavPath, name + ".wav")
        outputWavFN = join(outputPath, name + ".wav")
        
        # Sometimes the textgrid and wav file differ by some small amount
        # If the textgrid is longer, the script crashes
        wavDur = _getSoundFileDuration(wavFN)
        if entryList[-1][1] > wavDur and entryList[-1][0] < wavDur:
            entryList[-1] = (entryList[-1][0], wavDur, "")
        
        praatio_scripts.deleteWavSections(wavFN, outputWavFN, entryList,
                                          doShrink=False)


#def deleteUnlabeledIntervals(inputPath, tierName, outputPath):
#    """ 
#    Assumes TextGrid and wav files are inside same directory 
#    """
#    
#    deleteUnlabeledIntervals(inputPath, inputPath, tierName, outputPath)

#    utils.makeDir(outputPath)
#    
#    for name in utils.findFiles(inputPath,
#                                filterExt=".TextGrid",
#                                stripExt=True):
#        
#        tg = tgio.openTextGrid(join(inputPath, name + ".TextGrid"))
#        
#        # Get the unlabeled intervals
#        tier = tg.tierDict[tierName].fillInBlanks()
#        entryList = [entry for entry in tier.entryList
#                     if entry[2] == ""]
#        
#        wavFN = join(inputPath, name + ".wav")
#        outputWavFN = join(outputPath, name + ".wav")
#        
#        # Sometimes the textgrid and wav file differ by some small amount
#        # If the textgrid is longer, the script crashes
#        wavDur = _getSoundFileDuration(wavFN)
#        if entryList[-1][1] > wavDur and entryList[-1][0] < wavDur:
#            entryList[-1] = (entryList[-1][0], wavDur, "")
#        
#        praatio_scripts.deleteWavSections(wavFN, outputWavFN, entryList,
#                                          doShrink=False)


if __name__ == "__main__":
    
    _tgPath = r"/Users/authorofnaught/Desktop/TESTING/TEXTGRID"
    _wavPath = r"/Users/authorofnaught/Desktop/TESTING/WAV"
    _outputPath = r"/Users/authorofnaught/Desktop/TESTING/OUT"
    
    deleteUnlabeledIntervals(_tgPath, _wavPath, "Mother", _outputPath)
