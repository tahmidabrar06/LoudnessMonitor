import math
import pyaudio
import sys
import wave
from scipy.signal import butter, lfilter
import numpy
import tkinter as tk

class LoudnessMonitor:
    def __init__(self, volume=0.3, loudnessThreshhold=65, rate=44100, chunk=1024, cutoffFreq = 200):
        self.volume = volume
        self.loudnessThreshhold = loudnessThreshhold
        self.rate = rate
        self.chunk = chunk
        self.channels = 2
        self.format = pyaudio.paInt16
        self.cutoffFreq = cutoffFreq

        self.pyAudio = pyaudio.PyAudio()
        self.stream = self.pyAudio.open(format=self.format,
                                        channels=self.channels,
                                        rate=self.rate,
                                        frames_per_buffer=self.chunk,
                                        input=True,
                                        output=True)

        self.running = False
        self.decibel = 0
        #For testing
        self.chunksPerSec = (self.rate // self.chunk) // 10

    # Convert RMS to Decibel
    def calculateRms(self, audio_bytes):
        samples = numpy.frombuffer(audio_bytes, dtype=numpy.int16).astype(numpy.float32)
        return numpy.sqrt(numpy.mean(samples ** 2))
    
    def rms_to_dB(self, rms):
        if rms > 0:
            return 20 * math.log10(rms)
        else:
            return 1e-10

    # Set Volume
    def setVolume(self, sample):
        #Byte to numpy array
        nmArray = numpy.frombuffer(sample, dtype=numpy.int16)
        adjustedAudio = (nmArray * self.volume).astype(numpy.int16)
        return adjustedAudio.tobytes()

    # Play alert
    def beep(self):
        with wave.open(sys.path[0]+"\\beep.wav", 'rb') as wav:  
            p = pyaudio.PyAudio()
            alertStream = p.open(format=p.get_format_from_width(wav.getsampwidth()),
                            channels=wav.getnchannels(),
                            rate=wav.getframerate(),
                            output=True)

            while len(data := wav.readframes(self.chunk)):  
                alertStream.write(self.setVolume(data))
            alertStream.close()

    # Noise filter
    def highpass_filter(self, audio_bytes, order=5):
        audio_np = numpy.frombuffer(audio_bytes, dtype=numpy.int16)
        b, a = butter(order, self.cutoffFreq / (0.5 * self.rate), btype='high', analog=False)
        filtered = lfilter(b, a, audio_np)
        return filtered.astype(numpy.int16).tobytes()

    # Monitor Audio
    def monitor(self):
        counter = 0
        while self.running == True:
            data = self.stream.read(self.chunk)
            filtered = self.highpass_filter(data)
            rms = self.calculateRms(filtered)
            self.decibel = int(self.rms_to_dB(rms))
            # Output Audio (For Testing)
            #stream.write(data) 
            counter += 1
            if counter >= self.chunksPerSec:
                if self.decibel >= 0:
                    print(self.decibel)
                else:
                    print("0")
                counter = 0
                if self.decibel > self.loudnessThreshhold:
                    print("Too loud")
                    self.beep()
    
    # Start Monitoring
    def start(self):
        self.running = True
        self.monitor()

    # Stop Monitoring
    def stop(self):
        self.running = False

class GUI():
    def __init__(self):
        self.root = tk.Tk()
    def StartGUI(self):
        self.root.mainloop()
if __name__ == "__main__":
    LoudnessMonitor().start()
    #GUI().StartGUI()
