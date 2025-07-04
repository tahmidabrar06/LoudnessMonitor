import math
import pyaudio
import audioop
import sys

#loudness threshold in dB
loudnessThreshhold = 60

#Stream parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

pyAudio = pyaudio.PyAudio()
stream = pyAudio.open(format=FORMAT,
                      channels=CHANNELS,
                      rate=RATE,
                      frames_per_buffer=CHUNK,
                      input=True,
                      output=True)

#For testing, print decibel level every 'x' second
x = 10
chunks_per_second = (RATE // CHUNK) // x
counter = 0

#convert rms to decibel
def rms_to_dB(rms):
    if rms > 0:
        return 20 * math.log10(rms)
    else:
        return 1e-10

while True:
    data = stream.read(CHUNK)
    stream.write(data)
    rms = audioop.rms(data, 2)
    
    counter += 1
    if counter >= chunks_per_second:
        soundLevel = int(rms_to_dB(rms))
        print(soundLevel)
        counter = 0
        if soundLevel > loudnessThreshhold:
            print("Too loud")
            sys.exit()


