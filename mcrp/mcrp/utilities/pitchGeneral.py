
import os
from os.path import join
import io

import codecs
import shutil

from pyacoustics.utilities import utils

#from pyacoustics.textgrids import textgrids             # not used
#from pyacoustics.speech_rate import uwe_sr              # not used
from pyacoustics.signals import audio_scripts           # used in extractMotherSpeech and generateEpochFiles
from pyacoustics.intensity_and_pitch import praat_pi    # used in extractPraatPitchForEpochs
#from pyacoustics import aggregate_features              # not used

from praatio import tgio


def processTextgrids(path, tgFolder, includeMothersPhones=False):
    
    addEpochsToTextgrids(join(path, tgFolder),
                        join(path, "epochs"),
                        join(path, "textgrids_w_epochs"))

    renameTiers(join(path, "textgrids_w_epochs"),
                join(path, "textgrids_w_renamed_tiers"),
                includeMothersPhones
                )

    filterTextgrids(join(path, "textgrids_w_renamed_tiers"),
                    "Mother",
                    "Mother's Backchannel",
                    0.15,
                    join(path, "textgrids_w_epochs_final_non_isolated"))


#    # Removing ultrashort intervals, laughter segments, and intervals marked
#    # as pause
#    filterTextgrids(join(path, "textgrids_w_epochs"),
#                    "Mother",
#                    "Mother's Backchannel",
#                    0.15,
#                    join(path, "textgrids_w_epochs_filtered"))
#
#    # Unifying the tier names 
#    # (e.g. "Mother", "Mother's Speech", "mother speech" -> "Mother")
#    renameTiers(join(path, "textgrids_w_epochs_filtered"),
#                join(path, "textgrids_w_epochs_final_non_isolated"),
#                includeMothersPhones
#                )

# #     # Removing segments where the mother and child speech in unison
    isolateMotherSpeech(join(path, "textgrids_w_epochs_final_non_isolated"),
                        "Room",
                        join(path, "textgrids_w_epochs_filtered_for_room_noise")
                        )
# 
    isolateMotherSpeech(join(path, "textgrids_w_epochs_final_non_isolated"),
                        "Child",
                        join(path, "textgrids_w_epochs_filtered_for_child_speech")
                        )

    isolateMotherSpeech(join(path, "textgrids_w_epochs_filtered_for_room_noise"),
                        "Child",
                        join(path, "textgrids_w_epochs_filtered_for_room_noise_and_child_speech")
                        )
    
    finalSourceTextgridFolder = "textgrids_w_epochs_filtered_for_room_noise_and_child_speech"
    try:
        isolateMotherSpeech(join(path, "textgrids_w_epochs_filtered_for_room_noise_and_child_speech"),
                            "F0 Checks",
                            join(path, "textgrids_w_epochs_filtered_for_room_noise_child_speech_and_f0_checks"
                            ))
        finalSourceTextgridFolder = "textgrids_w_epochs_filtered_for_room_noise_child_speech_and_f0_checks"
    except KeyError:
        pass # No F0 checks done on these textgrids
    
# 
#     # Removing ultrashort segments created by the isolation function
    filterTextgrids(join(path, finalSourceTextgridFolder),
                    "Mother",
                    "Mother's Backchannel",
                    0.15,
                    join(path, "textgrids_w_epochs_final_isolated")
                    )

#     # Replaces all non-silence text with the label MS for "Mother Speech"
    replaceAllLabelsInMotherTierWithMS(join(path, "textgrids_w_epochs_final_isolated"),
                      join(path, "textgrids_two_tags")
                      )

    extractTGInfo(join(path, "textgrids_w_epochs_final_isolated"),
                  join(path, "tg_info"),
                  "Mother",
                  "Mother's Backchannel",
                  False)


def replaceAllLabelsInMotherTierWithMS(inputPath, outputPath):
    
    utils.makeDir(outputPath)
    
    speechTierName = "Mother"
    
    for fn in utils.findFiles(inputPath, filterExt=".TextGrid"):
        
        tg = tgio.openTextGrid(join(inputPath, fn))
        tg.replaceTier(speechTierName, [[start, stop, "MS"] for start, stop, label in tg.tierDict[speechTierName].entryList])
        tg.save(join(outputPath, fn))
        
    
def subtractOverlap(startTime, endTime, label, cmprStart, cmprEnd):
    
    returnList =[]
    if cmprStart <= startTime and cmprEnd >= endTime: # Crop entire region
        pass
    elif cmprStart <= startTime and cmprEnd < endTime: # Crop left edge
        returnList.append((cmprEnd, endTime, label))
    elif cmprStart > startTime and cmprEnd >= endTime: # Crop right edge
        returnList.append((startTime, cmprStart, label))
    elif cmprStart > startTime and cmprEnd < endTime: # Interval divided in two
        
        # If we have to divide the interval in two, only assign the label to one side
#        if cmprStart - startTime > cmprEnd - endTime: 
#            leftLabel = label
#            rightLabel = '(pST)'
#        else:
#            leftLabel = '(nST)'
#            rightLabel = label

        # Not sure why the above was the case - it left pST labels in the final textgrids, 
        # therefore rewritten here with the same code for both cases above (WAB) 
        leftLabel = label
        rightLabel = label
            
        returnList.append((startTime, cmprStart, leftLabel))
        returnList.append((cmprEnd, endTime, rightLabel))
    else: # No overlap
        returnList.append(startTime, endTime)    
    
    return returnList


def isolateMotherSpeech(path, filterGrid, outputPath):
    '''
    Removes mother speech when the child is also speaking
    '''
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(path, filterExt=".TextGrid"):
        
        tg = tgio.openTextGrid(join(path, fn))
        motherTier = tg.tierDict["Mother"]
        
        newEntryList = []
        for start, stop, label in motherTier.entryList:
            croppedTG = tg.crop(False, False, start, stop)
            entryList = croppedTG.tierDict[filterGrid].entryList
            
            resultList = [(start, stop, label),]
            
            for subStart, subStop, subLabel in entryList:
                
                i = 0
                while i < len(resultList):
                    tmpStart = resultList[i][0]
                    tmpEnd = resultList[i][1]
                    tmpResultList = subtractOverlap(tmpStart,
                                                    tmpEnd,
                                                    label,
                                                    subStart,
                                                    subStop)
                     # Replace if there has been a change
                    if tmpResultList != [[tmpStart, tmpEnd, label],]:
                        resultList = resultList[:i] + tmpResultList
                        i += len(tmpResultList) - 1
                    i += 1

            newEntryList.extend(resultList)

        newMotherTier = tgio.IntervalTier("Mother", newEntryList)
        tg.replaceTier("Mother", newMotherTier.entryList)
        tg.save(join(outputPath, fn))


def replaceTierName(tg, oldTierNameList, newTierName):
    
    for oldName in oldTierNameList:
        if oldName in tg.tierDict.keys():
            break
    
#    tierIndex = tg.tierNameList.index(oldName)
#    childsTier = tg.tierDict[oldName]
    
    tg.renameTier(oldName, newTierName)
    
    return tg


def renameTiers(inputPath, outputPath, includeMothersPhones=False):
    
    renameList = [(["Mother", "Mother's Speech", "Mother's speech", "mother's speech", "Mother Speech", "mother speech"], "Mother"),
                  (["Mother's Backchannel", "Mother's backchannel", "mother's backchannel", "child's backchannel"], "Mother's Backchannel"),
                  (["Child", "Child's speech", "Child's Speech", "child's speech", "Child Speech", "child speech"], "Child"),
                  (["Room", "Extraneous room noise", "Extraneous Room Noise", "Extraneous Noise", "Room Noise", "room noise", "Room noise", "extraneous room noise"], "Room"),
                  (["Timer", "Time"], "Timer"),
                  (["Epochs", "epochs",], "Epochs"),
                  ]
    
    if includeMothersPhones:
        renameList.insert(1, (["Mother's phones",], "Mother's Phones"))
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(inputPath, filterExt=".TextGrid"):
       
        print(fn) 
        tg = tgio.openTextGrid(join(inputPath, fn))
        
        for oldNameList, newName in renameList:
            try:
                tg = replaceTierName(tg, oldNameList, newName)
            except ValueError:
                print fn
                raise
        
        tg.save(join(outputPath, fn))


def addEpochsToTextgrids(tgPath, epochPath, outputPath):
    
    utils.makeDir(outputPath)
    
    for name in utils.findFiles(tgPath, filterExt=".TextGrid", stripExt=True):
        print name
        tg = tgio.openTextGrid(join(tgPath, name+".TextGrid"))

        entryList = utils.openCSV(epochPath, name+".txt")
        entryList = [(float(start), float(end), label) for label, start, end in entryList]
        
        tier = tgio.IntervalTier("epochs", entryList, minT=0, maxT=tg.maxTimestamp)
        
        tg.addTier(tier)
        tg.save(join(outputPath, name+".TextGrid"))
        
        
def insituLaughterCheck(start, stop, textgrid, laughterTierName):
    '''
    Returns True if there is no laughter during the interval.  False otherwise.
    '''
    croppedTG = textgrid.crop(strictFlag=False, softFlag=False, 
                              startTime=start, endTime=stop)
    tier = croppedTG.tierDict[laughterTierName]
    entryList = tier.getEntries()
    
    # Only intervals labeled "LA" are laughter
    entryList = [row for row in entryList if row[2].lower() == "la"]
    
    return len(entryList) == 0


def filterTextgrids(tgPath, speechTierName, laughterTierName, minDuration, outputPath):
    '''
    Removes invalid entries from the mother's speech tier
    
    - removes pauses (FP, SP)
    - removes speech (MS) that occurs with insitu laughter (LA)
    - removes ultrashort utterances (uwe's script crashed on an utterance of
                                     length 0.013 seconds)
    '''
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(tgPath, filterExt=".TextGrid"):
        
        tg = tgio.openTextGrid(join(tgPath, fn))

        # Removes all non-speech events (MS)
        newTierEntryList = []
        speechTier = tg.tierDict[speechTierName]
        for entry in speechTier.entryList:
            start, stop, label = entry
            print(entry)
            if insituLaughterCheck(start, stop, tg, laughterTierName):
               newTierEntryList.append(entry)
               
        # Removes all speech events shorter than some threshold
        newTierEntryList = [(start, stop, label) for start, stop, label in newTierEntryList
                            if float(stop) - float(start) > minDuration]
        tg.replaceTier(speechTierName, newTierEntryList)
        tg.save(join(outputPath, fn))
        

def eventStructurePerEpoch(epochPath, fullyFilteredTGPath, 
                           childFilteredTGPath, noiseFilteredTGPath,
                           unfilteredTGPath, outputPath, 
                           speechTierName, laughterTierName):
    '''
    How frequent and with what duration did laughter, pauses, and speech occur
    '''
    
    def _getCountsAndDurations(tier, searchLabel):
        entryList = tier.find(searchLabel)
        durationList = [float(stop) - float(start) 
                        for start, stop, label in entryList]
        count = len(entryList)
        
        return sum(durationList), count
    
    utils.makeDir(outputPath)
    
    for name in utils.findFiles(epochPath, filterExt=".txt", stripExt=True):
        
        epochList = utils.openCSV(epochPath, name+".txt")
        epochList = [(epochNum, float(start), float(stop)) 
                     for epochNum, start, stop in epochList]
        tg = tgio.openTextGrid(join(fullyFilteredTGPath, 
                                       name + ".TextGrid"))
        childFilteredTG = tgio.openTextGrid(join(childFilteredTGPath,
                                                   name + ".TextGrid"))
        noiseFilteredTG = tgio.openTextGrid(join(noiseFilteredTGPath,
                                                    name + ".TextGrid"))
        origTG = tgio.openTextGrid(join(unfilteredTGPath, 
                                           name + ".TextGrid"))
        
        outputList = []
        for epochNum, start, stop in epochList:
            subTG = tg.crop(strictFlag=False, softFlag=False, 
                            startTime=start, endTime=stop)
            
            speechTier = subTG.tierDict[speechTierName]
            laughterTier = subTG.tierDict[laughterTierName]
            
            pauseDur, numPauses = _getCountsAndDurations(speechTier, "FP")
            speechDur, numSpeech = _getCountsAndDurations(speechTier, "MS")
            laughDur, numLaughter = _getCountsAndDurations(laughterTier, "LA")
            
            subCSFilteredTG = childFilteredTG.crop(strictFlag=False, 
                                                softFlag=False,
                                                startTime=start,
                                                endTime=stop)
            csFilteredTier = subCSFilteredTG.tierDict[speechTierName]
            csFiltSpeech, numCSFiltSpeech = _getCountsAndDurations(csFilteredTier, 
                                                               "MS")            

            subNoiseFilteredTG = noiseFilteredTG.crop(strictFlag=False, 
                                                softFlag=False,
                                                startTime=start,
                                                endTime=stop)
            nsFilteredTier = subNoiseFilteredTG.tierDict[speechTierName]
            nsFiltSpeech, numNsFiltSpeech = _getCountsAndDurations(nsFilteredTier, 
                                                               "MS")     
            
            subOrigTG = origTG.crop(strictFlag=False,
                                    softFlag=False,
                                    startTime=start,
                                    endTime=stop)
            origSpeechTier = subOrigTG.tierDict[speechTierName]
            fullSpeechDur, fullNumSpeech = _getCountsAndDurations(origSpeechTier, 
                                                                  "MS")
            
            epochTuple = (speechDur, numSpeech, csFiltSpeech, nsFiltSpeech, 
                          fullSpeechDur, fullSpeechDur - speechDur,
                          pauseDur, numPauses, laughDur, numLaughter)
            outputList.append("%.02f, %d, %.02f, %.02f, %.02f, %.02f, %.02f, %d, %.02f, %d" % epochTuple)
        
        open(join(outputPath, name+".txt"), "w").write("\n".join(outputList) + "\n")
        
    
def analyzeLaughter(textgridPath, outputPath):
    
    utils.makeDir(outputPath)
    
    speechTierName = "Mother"
    laughterTierName = "Mother's Backchannel"
    
    speechCode = "MS"
    laughterCode = "LA"
    pauseCode = "FP"
    
    # How much did each event occur?
    allCodeSummaryList = []
    for tierName, code, outputName in [[speechTierName, speechCode, "speech_occurances"],
                                       [laughterTierName, laughterCode, "laughter_occurances"],
                                       [speechTierName, pauseCode, "pause_code"],
                                       ]:
        entryList = []
        summaryList = []
        for fn in utils.findFiles(textgridPath, filterExt=".TextGrid"):
            tg = tgio.openTextGrid(join(textgridPath, fn))
            tier = tg.tierDict[tierName]
            
            matchEntryList = tier.find(code)
            durationList = [float(stop)-float(start) for start, stop, label in matchEntryList]
            matchEntryList = [[fn,str(start),str(stop),label]for start, stop, label in matchEntryList] 
            
            entryList.extend(matchEntryList)
            summaryList.append( (fn, str(sum(durationList))) )
        
        entryList = [",".join(row) for row in entryList]
        open(join(outputPath, outputName+".csv"), "w").write("\n".join(entryList))

        allCodeSummaryList.append(summaryList)
    
    outputList = ["Filename,Speech,Laughter,Pause",]
    for speech, laugh, pause in utils.safeZip(allCodeSummaryList, enforceLength=True):
        outputList.append(",".join([speech[0], speech[1], laugh[1], pause[1]]))
        
    open(join(outputPath, "event_cumulative_lengths.csv"), "w").write("\n".join(outputList) + "\n")
        

def analyzeInsituLaughter(inputPath, outputPath):
    
    outputList = []
    for fn in utils.findFiles(inputPath, filterExt=".TextGrid"):
        
        tg = tgio.openTextGrid(join(inputPath, fn))
        tier = tg.tierDict["Mother"]
        for start, stop, label in tier.getEntries():
            isInsitu = insituLaughterCheck(start, stop, tg, "Mother's Backchannel")
            if isInsitu:
                outputList.append("%s,%02.02f,%02.02f,%s" % (fn, start, stop, label))
                
    open(join(outputPath, "insitu_laughter_events.csv"), "w").write("\n".join(outputList) + "\n")
        
       
def extractTGInfo(inputPath, outputPath, tierName, searchForMothersSpeech):
    '''
    Same as textgrids.extractTGInfo?
    

    '''
    
    utils.makeDir(outputPath)
    
    minDuration = 0.15 # Time in seconds
    
    
    for name in utils.findFiles(inputPath, filterExt=".TextGrid", stripExt=True):
        print name
        
        tg = tgio.openTextGrid(join(inputPath, name+".TextGrid"))
        tier = tg.tierDict[tierName]
        entryList = tier.getEntries()
        
        if searchForMothersSpeech:
            entryList = [(start, stop, label) for start, stop, label in entryList
                         if label == "MS"]
        
        outputList = []
        for start, stop, label in entryList:
            outputList.append( "%f,%f,%s" % (start, stop, label) )
            
        outputTxt = "\n".join(outputList) + "\n"
        codecs.open(join(outputPath, name + ".txt"), "w", encoding="utf-8").write(outputTxt)
        

def removeFilledPauses(inputPath, outputPath):
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(inputPath, filterExt=".txt"):
        dataList = utils.openCSV(inputPath, fn)
        dataList = [[start, stop, label] for start, stop, label in dataList if label == "MS"]
        dataList = [",".join(row) for row in dataList]
        open(join(outputPath, fn), "w").write("\n".join(dataList) + "\n")
        

def extractPraatPitchForEpochs(pitchPath, epochPath, tgInfoPath, outputPath):
    
    utils.makeDir(outputPath)
       
    for fn in utils.findFiles(pitchPath, filterExt=".txt"):
        name = os.path.splitext(fn)[0]
        
        print name

        epochList = utils.openCSV(epochPath, fn)
        epochList = [(epochNum, float(start), float(stop)) for epochNum, start, stop in epochList]
        
        entryList = utils.openCSV(tgInfoPath, fn)
        entryList = [(float(start), float(stop), label) for start, stop, label in entryList]
        
        dataList = praat_pi.loadPitchAndTime(pitchPath, fn)
        
        # Get F0 values for the intervals when the mother was speaking
        speechDataList = []
        for start, stop, label in entryList:
            speechDataList.extend(praat_pi.getAllValuesInTime(start, stop, dataList))
        
        # Get F0 values for the times the mother is speaking for each epoch
        pitchData = []
        for epochNum, start, stop in epochList:
            start, stop = float(start), float(stop)
            duration = stop - start
            epochValueList = praat_pi.getAllValuesInTime(start, stop, speechDataList)
            f0List = [f0Val for time, f0Val, intVal in epochValueList]
            
            pitchData.append(praat_pi.extractPitchMeasuresForSegment(f0List, name, epochNum, medianFilterWindowSize=None, filterZeroFlag=True))
        
        open(join(outputPath, "%s.txt" % name), "w").write("\n".join(pitchData) + "\n")
        

def extractMotherSpeech(wavPath, textgridPath, mothersSpeechName,
                        outputWavPath, outputTextgridPath):
    
    utils.makeDir(outputWavPath)
    utils.makeDir(outputTextgridPath)
    
    for name in utils.findFiles(wavPath, filterExt=".wav", stripExt=True,):
        print name
        tg = tgio.openTextGrid(join(textgridPath, name+".TextGrid"))
        speechTier = tg.tierDict[mothersSpeechName]
        for i, entry in enumerate(speechTier.entryList):
            subName = "%s_%03d" % (name, i)
            start, stop, label = entry
            start, stop = float(start), float(stop)
            audio_scripts.extractSubwav(join(wavPath, name+".wav"), 
                                        join(outputWavPath, subName+".wav" ),
                                             start, stop, 
                                             singleChannelFlag=True)
            subTG = tg.crop(strictFlag=False, softFlag=False, 
                            startTime=start, endTime=stop)
            subTG.save(join(outputTextgridPath, subName+".TextGrid"))


def generateEpochRowHeader(epochPath, outputPath, sessionCode):
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(epochPath, filterExt=".txt"):
        epochList = utils.openCSV(epochPath, fn)
        
        id = fn.split("_")[2]
        
        outputList = [",".join([id, sessionCode, epoch, epochStart, epochEnd, str(float(epochEnd) - float(epochStart))]) for epoch, epochStart, epochEnd in epochList]
        
        open(join(outputPath, fn), "w").write("\n".join(outputList) + "\n")


def adjustEpochNumbers(inputPath, outputPath):
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(inputPath, filterExt=".txt"):
        dataList = utils.openCSV(inputPath, fn)
        dataList = ["%02d,%s,%s" % (int(id)+1,start, stop) 
                    for id, start, stop in dataList]
        
        open(join(outputPath, fn), "w").write("\n".join(dataList) + "\n")

# Corresponding text files annotating the start and end times of each epoch 
# can be derived from textgrids.  The textgrids must have an interval tier 
# called "Epochs" which has been annotated with epoch intervals.
def generateEpochFiles(tgPath, wavPath, epPath):
    utils.makeDir(epPath)
    try:
        for filename in utils.findFiles(tgPath, filterExt=".TextGrid", stripExt=True):
            tgrid = tgio.openTextGrid(os.path.join(tgPath, filename+".TextGrid"))
            with open(os.path.join(epPath, filename+".txt"), "w") as epochFile:
                for (start,stop,label) in tgrid.tierDict["Epochs"].entryList:
                    epochFile.write(str(label)+','+str(start)+','+str(stop)+'\n')

    except:
        epDuration = int(raw_input("\nOk, the textgrids don't have an 'Epochs' tier.  How long are the epochs in this dataset?\nEnter the epoch duration in seconds: "))
        print("\nOk. Epochs are each %dsecs max.\n" % epDuration)    
#def generatePlayEpochs(path, outputPath):
    
        durationList = []
        for fn in utils.findFiles(wavPath, filterExt=".wav"):
            duration = audio_scripts.getSoundFileDuration(join(wavPath, fn))
            durationList.append( (fn, int(duration)) )
        
        durationList.sort()
        
        for fn, duration in durationList:
#            if '045' in fn:
#                print 'hello'
            outputFN = os.path.splitext(fn)[0] + ".txt"
            
            numEpoches = int(duration / epDuration)
            epochList = [(i, i*epDuration,(i+1)*epDuration) for i in xrange((numEpoches))]
            if duration % epDuration != 0:
                startTime = (numEpoches)*epDuration
                epochList.append( (numEpoches+1, startTime, startTime+(duration%epDuration) ) )
                
            epochList = ["%02d, %02d, %02d" % row for row in epochList]
            
            with open(join(epPath, outputFN), "w") as epochFN:
                epochFN.write("\n".join(epochList) + "\n")


def filterShortIntervalsFromTier(tgPath, speechTierName, minDuration, outputPath):
    '''
    Removes ultrashort utterances from tier (uwe's script crashed on an utterance of
                                     length 0.013 seconds)
    '''
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(tgPath, filterExt=".TextGrid"):
        
        tg = tgio.openTextGrid(join(tgPath, fn))
        speechTier = tg.tierDict[speechTierName]
        newTierEntryList = []

        for entry in speechTier.entryList:

            start, stop, label = entry

            if float(stop) - float(start) >= minDuration:

                newTierEntryList.append(entry)

        tg.replaceTier(speechTierName, newTierEntryList)
        tg.save(join(outputPath, fn))


def removeIntervalsFromTierByLabel(inputPath, tierName, targetLabel, outputPath, removeAllBut=False):
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(inputPath, filterExt=".TextGrid"):
        
        tg = tgio.openTextGrid(join(inputPath, fn))
        speechTier = tg.tierDict[tierName]
        newTierEntryList = []

        for entry in speechTier.entryList:

            start, stop, label = entry

            if removeAllBut and label == targetLabel:
                
                newTierEntryList.append(entry)

            elif not removeAllBut and label != targetLabel:

                newTierEntryList.append(entry)

        tg.replaceTier(tierName, newTierEntryList)
        tg.save(join(outputPath, fn))


# original code from Tim's uwe_sr.py
def aggregateSpeechRate(tgInfoPath, speechRatePath, outputPath, samplingRate):
    
    utils.makeDir(outputPath)
    
    finishedList = utils.findFiles(outputPath, filterExt=".txt")
    
    for fn in utils.findFiles(tgInfoPath, filterExt=".txt",
                              skipIfNameInList=finishedList):
        
        # Load subset speech rate
        name = os.path.splitext(fn)[0]
        speechRateFNList = utils.findFiles(speechRatePath, filterExt=".txt",
                                           filterPattern=name)
        
        subSplitList = utils.openCSV(tgInfoPath, fn)
    
        # Convert the sample numbers to seconds
        # They are in terms of the beginning of the subset they are in but
        # need to be in terms of the start of the file the larger file the
        # subset originated from
        outputList = []
        for splitInfo, speechRateFN in utils.safeZip([subSplitList,
                                                      speechRateFNList],
                                                     enforceLength=True):
            start, stop, label = splitInfo
            
            speechRateList = utils.openCSV(speechRatePath, speechRateFN, valueIndex=0)
            speechRateList = [value for value in speechRateList if value != '']
            speechRateList = [str(float(start) + float(sampleNum) / float(samplingRate)) for sampleNum in speechRateList]
            
            outputList.append( ",".join(speechRateList) )
    
        open(join(outputPath, fn), "w").write("\n".join(outputList) + "\n")
    

# original code from Tim's uwe_sr.py
def uwePhoneCountForEpochs(epochPath, tgInfoPath, manualCountsPath, outputPath):
    
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(tgInfoPath, filterExt=".txt"):
        print fn
        epochList = utils.openCSV(epochPath, fn)
        tgInfo = utils.openCSV(tgInfoPath, fn)
        manualCounts = utils.openCSV(manualCountsPath, fn)
        
        epochOutputList = []
        for epochNumber, epochStart, epochStop in epochList:
            epochStart, epochStop = float(epochStart), float(epochStop)
            
            # Find all of the intervals that are at least partially contained within
            # the current epoch
            epochSyllableCount = 0
            unadjustedEpochSyllableCount = 0
            epochArticulationRate = 0
            epochAverageSyllableDuration = 0
            for info, nucleusList in utils.safeZip([tgInfo, manualCounts],
                                                   enforceLength=True):
                start, stop, wordList = info
                start, stop = float(start), float(stop)
                
                syllableCount = len(nucleusList)
                unadjustedEpochSyllableCount += syllableCount
                # Accounts for intervals that straddle an epoch boundary
                multiplicationFactor = _percentInside(start, stop, epochStart,
                                                      epochStop)
                
                epochSyllableCount += syllableCount * multiplicationFactor
            
#             epochOutputList.append("%f,%f" % (unadjustedEpochSyllableCount,epochSyllableCount))
            epochOutputList.append("%f" % (epochSyllableCount))
                    
        open(join(outputPath, fn), "w").write("\n".join(epochOutputList) + "\n")
        

# original code from Tim's uwe_sr.py        
def _percentInside(startTime, endTime, cmprStartTime, cmprEndTime):
    
    if (float(startTime) <= float(cmprEndTime) and 
            float(endTime) >= float(cmprStartTime)):

        leftEdge = cmprStartTime - startTime
        rightEdge = endTime - cmprEndTime
        
        if leftEdge < 0:
            leftEdge = 0
        if rightEdge < 0:
            rightEdge = 0
            
        retVal = 1 - ((rightEdge + leftEdge)) / (endTime - startTime)

    # No overlap
    else:
        retVal = 0

    return retVal


# original code from Tim's pyacoustics/aggregate_features.py
def aggregateFeatures(featurePath, featureList, outputDirName, headerStr=None):
    
    outputDir = join(featurePath, outputDirName)
    utils.makeDir(outputDir)
    
    fnList = []
    dataList = []
    
    # Find the files that exist in all features
    for feature in featureList:
        fnSubList = utils.findFiles(join(featurePath, feature),
                                    filterExt=".txt")
        fnList.append(fnSubList)
        
    actualFNList = []
    for featureFN in fnList[0]:
        if all([featureFN in subList for subList in fnList]):
            actualFNList.append(featureFN)
    
    for featureFN in actualFNList:
        dataList = []
        for feature in featureList:
            featureDataList = utils.openCSV(join(featurePath, feature),
                                            featureFN, encoding="utf-8")
            dataList.append([",".join(row) for row in featureDataList])
        
        name = os.path.splitext(featureFN)[0]
        
        dataList.insert(0, [name for _ in range(len(dataList[0]))])
        tDataList = utils.safeZip(dataList, enforceLength=True)
        outputList = [",".join(row) for row in tDataList]
        outputTxt = "\n".join(outputList)
        
        outputFN = join(outputDir, name + ".csv")
        with io.open(outputFN, "w", encoding="utf-8") as fd:
            fd.write(outputTxt)
        
    # Cat all files together
    aggrOutput = []
    
    if headerStr is not None:
        aggrOutput.append(headerStr)
    
    for fn in utils.findFiles(outputDir, filterExt=".csv"):
        if fn == "all.csv":
            continue
        with io.open(join(outputDir, fn), "r", encoding='utf-8') as fd:
            aggrOutput.append(fd.read())
    
    with io.open(join(outputDir, "all.csv"), "w", encoding='utf-8') as fd:
        fd.write("\n".join(aggrOutput))
