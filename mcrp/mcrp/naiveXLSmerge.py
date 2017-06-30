import os
from csvxls import *
from os.path import join, splitext, isdir, basename
import utilities.mcrp_io as io

#
# NaiveXLSmerge.py
# @author Bill Bryce(authorofnaught@gmail.com)
# @version Oct 25, 2015
#
# Takes any files within the INPUT directory inside this directory
# and attempts to merge them under two naive assumptions:
# 1) That all files are Excel workbooks coding the same session (Play, Puzzle1, Puzzle2, etc.)
# 2) That all workbooks have the exact same fieldnames
#

def merge(indir_path, outdir_path):

#  indir_path = join(path, 'INPUT')
#  outdir_path = join(path, 'OUTPUT')

#  if not isdir(outdir_path):
#    os.mkdir(outdir_path)

  io.make_dir(outdir_path)
  
  mastercsv_path = ''
  output_fields = []
  num_files = 0
  for filename in os.listdir(indir_path):
    if filename.endswith('.xls') or filename.endswith('.xlsx'): 
      inxls_path = join(indir_path, filename)
      outcsv_path = join(indir_path, splitext(filename)[0]+'.csv')
      XLStoCSV(inxls_path, outcsv_path)
      if num_files == 0:
        mastercsv_path = join(outdir_path, splitext(filename)[0]+'Master.csv')
        with open(outcsv_path, "rb") as csvfile:
          reader = csv.DictReader(csvfile)
          output_fields = reader.fieldnames
      num_files+=1

  with open(mastercsv_path, "wb") as outcsv:
    writer = csv.DictWriter(outcsv, output_fields)
    writer.writeheader()
    for filename in os.listdir(indir_path):
      if filename.endswith('.csv'):
        with open(join(indir_path, filename)) as csvpath:
          reader = csv.DictReader(csvpath)
          for row in reader:
            writer.writerow(row)
        os.remove(join(indir_path, filename))

  masterxls_path = splitext(mastercsv_path)[0]+'.xlsx'
  CSVtoXLS(mastercsv_path, masterxls_path, grid=True, wrap=True)
  try:
    setXLSColumnWidthByLabel(masterxls_path, 'Notes1', 60.0)
    setXLSColumnWidthByLabel(masterxls_path, 'Notes2', 60.0)
  except:
    pass
  os.remove(mastercsv_path)
  
  print("\tDone.\n\t{}\n\toutput to\n\t{}".format(
          basename(masterxls_path), outdir_path))      



#if __name__ == '__main__':

  # Set path to folder containing INPUT subfolder.  
  # An OUTPUT subfolder will be created here, if one does not already exist.
#  path = r'/Users/authorofnaught/Projects/Maternal_Prosody/scripts.git/NaiveXLSmerge'
#  path = r"S:\HCD Faculty Staff Projects\McElwain-MCRP\PYTHON_SCRIPTS\NaiveXLSmerge"

#  naiveXLSmerge(path)

