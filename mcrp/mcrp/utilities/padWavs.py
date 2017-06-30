import sys
import wave
from praatio.utilities import utils
from os.path import join

def padEndWithSilence(indir, outdir):
    
    utils.makeDir(outdir)
    
    for name in utils.findFiles(indir,
                                filterExt=".wav",
                                stripExt=False):

        inwavfile = join(indir, name)
        outwavfile = join(outdir, name)

        inwav = wave.open(inwavfile, 'rb')
        outwav = wave.open(outwavfile, 'wb')

        data = inwav.readframes(inwav.getnframes())
        silence = '\x00' * 200000
        outdata = data + silence
        
        outwav.setnchannels(inwav.getnchannels())
        outwav.setsampwidth(inwav.getsampwidth())
        outwav.setframerate(inwav.getframerate())
        outwav.setcomptype('NONE','not compressed')
        outwav.writeframes(outdata)

        inwav.close()
        outwav.close()

if __name__ == '__main__':

    indir = "/Users/authorofnaught/Desktop/TESTING/WAV"
    outdir = "/Users/authorofnaught/Desktop/TESTING/OUT"
    padEndWithSilence(indir, outdir)
