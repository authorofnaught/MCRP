import sys
import os
import shutil
from os.path import join
from collections import defaultdict


def has_an_ext(filepath): 

	return not os.path.splitext(filepath)[1] == ""


def get_files_w_ext(dirpath, ext):

	filelist = []
	for fn in os.listdir(dirpath):
		if os.path.isfile(os.path.join(dirpath, fn)) and fn.endswith(ext):
			filelist.append(os.path.join(dirpath, fn))
	return filelist


def get_filename_w_new_ext(filepath, ext):

	if has_an_ext(filepath):
		filebase = os.path.splitext(filepath)[0]
		if ext.startswith('.'):
			return filebase+ext
		else:
			return filebase+'.'+ext
	else:
		print("File {} has no extension to replace".format(filepath))
		return filepath


def make_dir(dirpath, overwrite=False):

	if os.path.exists(dirpath) and overwrite:
		shutil.rmtree(dirpath)
		os.makedirs(dirpath)
	elif not os.path.exists(dirpath):
		os.makedirs(dirpath)
		
