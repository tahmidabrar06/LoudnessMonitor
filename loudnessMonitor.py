import math
import pyaudio
import audioop
import sys
import wave
from scipy.signal import butter, lfilter
import numpy

volume = 0.2
#loudness threshold in dB
loudnessThreshhold = 65

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

#Set Volume
def adjustVolume(sample):
    #Byte to numpy array
    nmArray = numpy.frombuffer(sample, dtype=numpy.int16)
    adjustedAudio = (nmArray * volume).astype(numpy.int16)
    return adjustedAudio.tobytes()

#play alert
def beep():
    with wave.open(sys.path[0]+"\\beep.wav", 'rb') as wf:
        
        p = pyaudio.PyAudio()

        alertStream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True) #Output for testing

        while len(data := wf.readframes(CHUNK)):  
            alertStream.write(adjustVolume(data))
        alertStream.close()

#noise filter
def highpass_filter(audio_bytes, cutoffFreq=200, freq=RATE, order=5):
    audio_np = numpy.frombuffer(audio_bytes, dtype=numpy.int16)
    b, a = butter(order, cutoffFreq / (0.5 * freq), btype='high', analog=False)
    filtered = lfilter(b, a, audio_np)
    return filtered.astype(numpy.int16).tobytes()

if __name__ == "__main__":
    volume = float(input("Set alert volume: "))
    threshhold = (input("Set loudness threshhold (default 65 dB, leave empty for default): "))
    if threshhold != "":
        loudnessThreshhold = int(threshhold)
    while True:
        data = stream.read(CHUNK)
        filtered_data = highpass_filter(data)
        rms = audioop.rms(filtered_data, 2)
        #stream.write(data) 
        soundLevel = int(rms_to_dB(rms))
        counter += 1
        if counter >= chunks_per_second:
            print(soundLevel)
            counter = 0
            if soundLevel > loudnessThreshhold:
                print("Too loud")
                beep()
