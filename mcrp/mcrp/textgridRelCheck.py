'''TextGridReliabilityCheck.py

@author: Tim Mahrt (tmahrt)
@version: 2016-09-09

Compares two textgrids and outputs a textgrid with all the differences between them
and a textfile with the differences listed line by line

@author: Bill Bryce (authorofnaught): 
@version: 2016-10-05

The original script reported differences in annotation exactly.  The script now has 
a leeway parameter which excludes intervals of difference smaller than this leeway 
value. For instance, if leewayInMs=100, then any interval on the diffTG smaller than 
100ms is not considered a difference in annotation.

Also modified to produce "report" output and to include in that output annotator 
agreement on Mother tier when Mother tier intervals overlapping with intervals on
Room and Child tiers have been cropped.

Annotator agreement in the report is given as both proportion of annotation shared
by both annotators and as precision and recall of "hits" and "misses" - a "hit"
is a tier interval annotated by annotator A which was also annotated by annotator B
whose start and ends times fall within the leeway parameter; otherwise the 
annotated interval is counter as a miss.
'''

import os
import re
from praatio import tgio
import tempfile
import shutil
from collections import defaultdict
import utilities.mcrp_io as io


def _tgAsText(tg, tg1Name, tg2Name):
	
	outputList = []
	for tierName in tg.tierNameList:
		
		tier = tg.tierDict[tierName]
		
		for entry in tier.entryList:
			outputList.append([tg1Name, tg2Name, tierName, ] + list(entry))
		
	return outputList


def _tierAnnotationInSecs(tier):

	totalTime = 0.0
	entries = tier.entryList
	for entry in entries:
		start, stop, _ = entry
		time = stop - start
		totalTime += time
	return totalTime


def _getDiffTier(tier1, tier2, leewayInSecs):

	diffTier = tier1.union(tier2)

	entries2delete = []
	for entry in diffTier.entryList:
		start, stop, _ = entry
		if (stop - start) < leewayInSecs:
			entries2delete.append(entry)
	for entry in entries2delete:
		diffTier.deleteEntry(entry)

	return diffTier


def compareTGs(baseTGFN, compareTGFN, outputBasename, textgridPath, tgtextPath, reportPath, 
				tierList=None, leewayInMS=0.0, report_misslist=False):
	
	baseTGname = os.path.splitext(os.path.split(baseTGFN)[1])[0]
	compareTGname = os.path.splitext(os.path.split(compareTGFN)[1])[0]
	
	report = "Annotation comparison report for the follwing two textgrids: \
					\n\t{}\n\t{}\n\n".format(baseTGname, compareTGname)
	report += "Differences within {}MS not reported\n\n".format(leewayInMS)
#	report += "KEY:\n"
#	report += "\tproportion agreement = proportion of area annotated by both annotators;\
#					\n\t\thas nothing to do with interval boundaries\n"
#	report += "\tproportion disagreement = proportion of area annotated by one annotator but not both\n"
#	report += "\thits = # of intervals marked similarly by both annotators\n"
#	report += "\tmisses = # of intervals overlapping, but with suffieciently different annotated boundaries\n"
#	report += "\tno_overlap = extra intervals from one annotator or the other\n"
#	report += "\textra_tg1 = extra intervals at the end of textgrid#1\n"
#	report += "\textra_tg2 = extra intervals at the end of textgrid#2\n"
#	report += "\thit agreement only extras = ( hits / ( hits + no_overlaps + extra_tg1 + extra_tg2 ) )\n"
#	report += "\thit agreement no extras = ( hits / ( hits + misses ) )\n"
#	report += "\thit agreement general = ( hits / ( hits + misses + no_overlaps + extra_tg1 + extra_tg2 ) )\n"
	report += "\n"
	report += "ANNOTATION COMPARISON BY TIER:\n\n"

	baseTG = tgio.openTextGrid(baseTGFN)
	compareTG = tgio.openTextGrid(compareTGFN)

	misslist = "LIST OF MISSES BY TIER:\n\n"

	leewayInSecs = (leewayInMS / 1000.0)
	
	if tierList is None:
		tierList = baseTG.tierNameList
	
	assert "Mother" in tierList
	assert "Child" in tierList
	assert "Room" in tierList

	diffTG = tgio.Textgrid()
	diffTG1 = tgio.Textgrid()
	diffTG2 = tgio.Textgrid()

	for tierName in tierList:
		
		report += "\tTIER = {}\n".format(tierName)
		misslist += "\tTIER = {}\n".format(tierName)

		baseTier = baseTG.tierDict[tierName]
		compareTier = compareTG.tierDict[tierName]

		diffTier1 = baseTier.difference(compareTier)
		diffTier2 = compareTier.difference(baseTier)
		diffTier = _getDiffTier(diffTier1, diffTier2, leewayInSecs)

		baseTime = _tierAnnotationInSecs(baseTier)
		compareTime = _tierAnnotationInSecs(compareTier)
		diffTime = _tierAnnotationInSecs(diffTier)
		unionTime = _tierAnnotationInSecs(baseTier.union(compareTier))
		disagreement = ( diffTime / unionTime ) if unionTime != 0 else 0.0
		agreement = ( ( unionTime - diffTime) / unionTime ) if unionTime != 0 else 0.0
		disagreementLocs = []
		for entry in diffTier.entryList:
			start, stop, _ = entry
			disagreementLocs.append("{} - {}".format(start, stop))

		report += "\tnumber of intervals in {}: {}\n".format(baseTGname, len(baseTier.entryList))
		report += "\tnumber of intervals in {}: {}\n".format(compareTGname, len(compareTier.entryList))
		report += "\tproportion agreement = {}\n\tproportion disagreement = {}\n".format(agreement, disagreement)
		rep, misses = getHitReport(baseTGname, compareTGname, baseTier.entryList, compareTier.entryList, leewayInMS)
		report += rep
		misslist += misses+'\n\n'
#		report += "\tlocations of disagreement:\n\t\t{}\n\n\n".format("\n\t\t".join(disagreementLocs))
		report += "\n\n"
		
		diffTG1.addTier(diffTier1)
		diffTG2.addTier(diffTier2)
		diffTG.addTier(diffTier)
		
	report += "ANNOTATION COMPARISON OF \"Mother\" WITH \"Child\" AND \"Room\" REMOVED:\n\n"
	misslist += "MISSES ON \"Mother\" WITH \"Child\" AND \"Room\" REMOVED:\n\n"

	TMP = tempfile.mkdtemp()
	for tier in ["Child", "Room"]:

		newTGFN = os.path.join(TMP, '_'.join([tier, baseTGname]))
		isolateMotherSpeech(baseTGFN, tier, newTGFN)
		baseTGFN = newTGFN

		newTGFN = os.path.join(TMP, '_'.join([tier, compareTGname]))
		isolateMotherSpeech(compareTGFN, tier, newTGFN)
		compareTGFN = newTGFN

	baseTG = tgio.openTextGrid(baseTGFN)
	compareTG = tgio.openTextGrid(compareTGFN)

	baseTier = baseTG.tierDict["Mother"]
	compareTier = compareTG.tierDict["Mother"]

	diffTier1 = baseTier.difference(compareTier)
	diffTier2 = compareTier.difference(baseTier)
	diffTier = _getDiffTier(diffTier1, diffTier2, leewayInSecs)

	baseTime = _tierAnnotationInSecs(baseTier)
	compareTime = _tierAnnotationInSecs(compareTier)
	diffTime = _tierAnnotationInSecs(diffTier)
	unionTime = _tierAnnotationInSecs(baseTier.union(compareTier))
	disagreement = ( diffTime / unionTime )
	agreement = ( ( unionTime - diffTime) / unionTime )
	disagreementLocs = []
	for entry in diffTier.entryList:
		start, stop = entry[:2]
		disagreementLocs.append("{} - {}".format(start, stop))
	
	report += "\tnumber of intervals in {}: {}\n".format(baseTGname, len(baseTier.entryList))
	report += "\tnumber of intervals in {}: {}\n".format(compareTGname, len(compareTier.entryList))
	report += "\tproportion agreement = {}\n\tproportion disagreement = {}\n".format(agreement, disagreement)
	rep, misses = getHitReport(baseTGname, compareTGname, baseTier.entryList, compareTier.entryList, leewayInMS)
	report += rep
	misslist += misses+'\n\n'
#	report += "\tlocations of disagreement:\n\t\t{}\n\n\n".format("\n\t\t".join(disagreementLocs))
	report += "\n\n"

	if report_misslist:
		report += misslist

	report += "END OF REPORT\n"

	shutil.rmtree(TMP)

	# Write the three output files	  
	outputTGFN = os.path.join(textgridPath, outputBasename+".TextGrid")
	outputTXTFN = os.path.join(tgtextPath, outputBasename+".TG.txt")
	outputREP = os.path.join(reportPath, outputBasename+".REPORT.txt")

	diffTG.save(outputTGFN)

	with open(outputTXTFN, 'w') as outtxt:
		retTxt = _tgAsText(diffTG1, baseTGname, compareTGname)
		retTxt += _tgAsText(diffTG2, compareTGname, baseTGname)
		for txt in retTxt:
			outtxt.write('\t'.join([str(item) for item in txt])+'\n')

	with open(outputREP, 'w') as outtxt:
		outtxt.write(report)	



def getHitReport(TG1name, TG2name, TG1entryList, TG2entryList, leewayInSecs):

	rep1, misslist1, prec1, rec1, F1 = compareTierEntries(TG1name, TG2name, TG1entryList, TG2entryList, leewayInSecs)
	rep2, misslist2, prec2, rec2, F2 = compareTierEntries(TG2name, TG1name, TG2entryList, TG1entryList, leewayInSecs)
	try: 
		mean_string = "\tmean results:\n\t\tprecision =\t\t{}\n\t\trecall =\t\t{}\n\t\tF-measure =\t\t{}\n".format(
			( ( prec1 + prec2 ) / 2.0 ), ( ( rec1 + rec2 ) / 2.0 ), ( ( F1 + F2 ) / 2.0 ))
	except TypeError:
		mean_string = "\tmean results:\n\t\tprecision =\t\t{}\n\t\trecall =\t\t{}\n\t\tF-measure =\t\t{}\n".format(
			prec1, rec1, F1)
	return ( rep1 + rep2 + mean_string ), ( misslist1 + misslist2 )


def compareTierEntries(baseTGname, compareTGname, baseEntryList, compareEntryList, leewayInSecs):

	report = ""
	misslist = ["\t{}\n\t{}\t::\t{}\t::\ttype\n\t{}".format(
		"-"*70, baseTGname, compareTGname, "-"*70)]
	tp = 0.0
	fp = 0.0
	baseEntries = iter(baseEntryList)
	compareEntries = iter(compareEntryList)

	baseEntry = next(baseEntries, None)
	compareEntry = next(compareEntries, None)
	while baseEntry and compareEntry:
		if overlaps(baseEntry, compareEntry):
			if isHit(baseEntry, compareEntry, leewayInSecs):
				tp+=1
				misslist.append("\t{}--{}\t::\t{}--{}\t::\tHIT".format(
					"%.5f" % baseEntry[0], "%.5f" % baseEntry[1], "%.5f" % compareEntry[0], "%.5f" % compareEntry[1]))
				baseEntry = next(baseEntries, None)
				compareEntry = next(compareEntries, None)
			else:
				fp+=1
				misslist.append("\t{}--{}\t::\t{}--{}\t::\tMISS".format(
					"%.5f" % baseEntry[0], "%.5f" % baseEntry[1], "%.5f" % compareEntry[0], "%.5f" % compareEntry[1]))
				if baseEntry[1] <= compareEntry[1]:
					baseEntry = next(baseEntries, None)
					if baseEntry[0] >= compareEntry[1]:
						compareEntry = next(compareEntries, None)
				elif baseEntry[1] > compareEntry[1]:
					compareEntry = next(compareEntries, None)
					if baseEntry[1] <= compareEntry[0]:
						baseEntry = next(baseEntries, None)
				else:
					print("\tERROR: Should have been a hit, but was not.")
					print("\t{} in {}".format(baseEntry, baseTGname))
					print("\t{} in {}".format(compareEntry, compareTGname))
					break
		else:
			fp+=1
			misslist.append("\t{}--{}\t::\t{}--{}\t::\tNO_OVERLAP".format(
				"%.5f" % baseEntry[0], "%.5f" % baseEntry[1], "%.5f" % compareEntry[0], "%.5f" % compareEntry[1]))
			if baseEntry[1] <= compareEntry[1]:
				baseEntry = next(baseEntries, None)
				if baseEntry and baseEntry[0] >= compareEntry[1]:
					compareEntry = next(compareEntries, None)
			elif baseEntry[1] > compareEntry[1]:
				compareEntry = next(compareEntries, None)
				if compareEntry and baseEntry[1] <= compareEntry[0]:
					baseEntry = next(baseEntries, None)
	while baseEntry:
		fp+=1
		misslist.append("\t{}--{}\t::\tNONE--NONE\t::\tEXTRA_IN_TG1".format(
			"%.5f" % baseEntry[0], "%.5f" % baseEntry[1]))
		baseEntry = next(baseEntries, None)
	while compareEntry:
		fp+=1
		misslist.append("\tNONE--NONE\t::\t{}--{}_EXTRA_IN_TG2".format(
			"%.5f" % compareEntry[0], "%.5f" % compareEntry[1]))
		compareEntry = next(compareEntries, None)

	report += "\thit metrics for {} compared to {}\n".format(baseTGname, compareTGname)
	report += "\t\thits =\t\t\t{}\n".format(int(tp))
	report += "\t\tmisses =\t\t{}\n".format(int(fp))
	try:
		precision = ( tp / ( tp + fp ) )
	except ZeroDivisionError:
		precision = 0.0
	try:
		recall = ( tp / len(compareEntryList) )
	except ZeroDivisionError:
		recall = 0.0
	try:	
		F1 = 2.0 * ( ( precision * recall ) / ( precision + recall ) )
	except ZeroDivisionError:
		F1 = 0.0

	report += "\t\tprecision =\t\t{}\n\t\trecall =\t\t{}\n\t\tF-measure =\t\t{}\n".format(
		precision, recall, F1)

	return report, '{}\n'.format('\n'.join(misslist)), precision, recall, F1


		
def isHit(entry1, entry2, leewayInSecs):
	
	start1, end1 = entry1[:2]
	start2, end2 = entry2[:2]

	startTimesOK = abs(start1 - start2) < leewayInSecs
	endTimesOK = abs(end1 - end2) < leewayInSecs
	return (startTimesOK and endTimesOK)



def overlaps(entry1, entry2):

	start1, end1, _ = entry1
	start2, end2, _ = entry2

	overlapTime = max(0, min(end1, end2) -
					  max(start1, start2))
	return overlapTime > 0



def isolateMotherSpeech(path, filterGrid, outputPath):
	'''
	Removes mother speech when the child is also speaking
	'''

	tg = tgio.openTextGrid(path)
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
	tg.save(outputPath)


def subtractOverlap(startTime, endTime, label, cmprStart, cmprEnd):

	returnList =[]
	if cmprStart <= startTime and cmprEnd >= endTime: # Crop entire region
		pass
	elif cmprStart <= startTime and cmprEnd < endTime: # Crop left edge
		returnList.append((cmprEnd, endTime, label))
	elif cmprStart > startTime and cmprEnd >= endTime: # Crop right edge
		returnList.append((startTime, cmprStart, label))
	elif cmprStart > startTime and cmprEnd < endTime: # Interval divided in two

		# Not sure why the above was the case - it left pST labels in the final textgrids, 
		# therefore rewritten here with the same code for both cases above (WAB) 
		leftLabel = label
		rightLabel = label

		returnList.append((startTime, cmprStart, leftLabel))
		returnList.append((cmprEnd, endTime, rightLabel))
	else: # No overlap
		returnList.append(startTime, endTime)

	return returnList


def textgridReliabilityCheck(indirpath, outdirpath, leeway_in_MS, add_misslist, overwrite, compare_in_pairs=True):

	session_pattern = re.compile(r"(MCRP_ID#[0-9]+_[A-Z0-9]+)_[A-Z]+.TextGrid")
	coder_pattern = re.compile(r"MCRP_ID#[0-9]+_[A-Z0-9]+_([A-Z]+).TextGrid")

	compareList = []
	tgDict = defaultdict(list)

	filelist = io.get_files_w_ext(indirpath, "TextGrid")

	for tgfn in filelist:
		session = re.search(session_pattern, tgfn).group(1)
		tgDict[session].append(tgfn)

	for sess in tgDict.keys():
		session = tgDict.pop(sess)
		if not compare_in_pairs:
			compareList.append(tuple(session))
		else:
			while len(session) > 0:
				c1 = session.pop(0)
				for i in range(len(session)):
					c2 = session[i]
					compareList.append((c1,c2))

	textgridPath = os.path.join(outdirpath, "textgrid")
	tgtextPath = os.path.join(outdirpath, "tgText")
	reportPath = os.path.join(outdirpath, "report")
	io.make_dir(textgridPath, overwrite)
	io.make_dir(tgtextPath, overwrite)
	io.make_dir(reportPath, overwrite)

	for tg1, tg2 in compareList:

		print("Processing reliability of annotations in\n\t{} :: {}".format(os.path.basename(tg1), os.path.basename(tg2)))

		session1 = re.search(session_pattern, tg1).group(1)
		session2 = re.search(session_pattern, tg2).group(1)
		try:
			assert session1 == session2
		except AssertionError:
			print("Tried to process two files encoding different sessions: \
						\n{}\n{}".format(session1, session2))
		coder1 = re.search(coder_pattern, tg1).group(1)
		coder2 = re.search(coder_pattern, tg2).group(1)

		fn1 = os.path.join(indirpath, tg1)
		fn2 = os.path.join(indirpath, tg2)
		outfn = "_".join([session1, coder1, coder2])+".RelCheck"
		compareTGs(fn1, fn2, outfn, textgridPath, tgtextPath, reportPath, 
					leewayInMS=leeway_in_MS, report_misslist=add_misslist)
			
	print("Done. The output is in...\n{}".format(outdirpath))

