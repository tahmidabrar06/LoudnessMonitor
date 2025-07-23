import math
import pyaudio
import sys
import wave
from scipy.signal import butter, lfilter
import numpy
import tkinter as tk
from tkinter import Scale
import threading

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
            alertStream = self.pyAudio.open(format=self.pyAudio.get_format_from_width(wav.getsampwidth()),
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
                    threading.Thread(target=self.beep, daemon=True).start()
    
    # Start Monitoring
    def start(self):
        self.running = True
        self.monitor()

    # Stop Monitoring
    def stop(self):
        self.running = False

class GUI():
    def __init__(self, loudnessMonitor):
        self.root = tk.Tk()
        self.loudnessMonitor=loudnessMonitor
        # Font
        self.paramemterFont = ("Arial", 10)
        self.buttonFont = ("Arial", 10)

        # LoudnessMonitor Paramters
        self.volumeSlider = Scale(self.root, from_=100, to=0)
        self.volumeSlider.pack()
        self.volume = tk.Label(self.root, text="Volume", font=self.paramemterFont)
        self.volume.pack()

        self.loudnessThresholdSlider = Scale(self.root, from_=120, to=1)
        self.loudnessThresholdSlider.pack()
        self.loudnessThreshold = tk.Label(self.root, text="Threshold (dB)", font=self.paramemterFont)
        self.loudnessThreshold.pack()

        # Buttons
        self.startButton = tk.Button(self.root, text="Start", font=self.buttonFont, command=self.startLoudnessMonitor)
        self.startButton.pack()

        self.stopButton = tk.Button(self.root, text="Stop", font=self.buttonFont, command=self.stopLoudnessMonitor, state="disabled")
        self.stopButton.pack()

    # Update LoudnessMonitor parameters
    def setParameters(self):
        self.loudnessMonitor.volume = self.volumeSlider.get() / 100
        self.loudnessMonitor.loudnessThreshhold = self.loudnessThresholdSlider.get()

    # Start Loudness Monitor
    def startLoudnessMonitor(self):
        self.setParameters()
        if not self.loudnessMonitor.running:
            monitor_thread = threading.Thread(target=self.loudnessMonitor.start, daemon=True)
            monitor_thread.start()
        self.startButton.config(state="disabled")
        self.stopButton.config(state="normal")
        self.volumeSlider.config(state="disabled")
        self.loudnessThresholdSlider.config(state="disabled")

    # Stop Loudness Monitor
    def stopLoudnessMonitor(self):
        self.loudnessMonitor.stop()
        self.startButton.config(state="normal")
        self.stopButton.config(state="disabled")
        self.volumeSlider.config(state="normal")
        self.loudnessThresholdSlider.config(state="normal")

    # Start GUI
    def startGUI(self):
        self.root.geometry("800x500")
        self.root.mainloop()

if __name__ == "__main__":
    loudnessMonitor = LoudnessMonitor()
    GUI(loudnessMonitor).startGUI()
