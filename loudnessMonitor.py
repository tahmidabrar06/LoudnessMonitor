import math
import pyaudio
import sys
import os
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

        # Set path so its compatible with PyInstaller
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        beep_path = os.path.join(base_path, 'beep.wav')

        with wave.open(beep_path, 'rb') as wav:
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
        self.root.title("Loudness Monitor")

        # Set path so its compatible with PyInstaller
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        iconPath = os.path.join(base_path, 'icon.ico')
        self.root.iconbitmap(iconPath)

        # Font
        self.paramemterFont = ("Arial", 10)
        self.buttonFont = ("Arial", 10)

        # Slider Frame
        self.frame = tk.Frame(self.root)

        # Configure Slider Grid
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(2, weight=1)

        # Volume Slider and Label
        self.volumeSlider = Scale(self.frame, from_=100, to=0)
        self.volumeSlider.grid(row=0, column=0)
        self.volume = tk.Label(self.frame, text="Volume", font=self.paramemterFont)
        self.volume.grid(row=1, column=0)

        # Threshold Slider and Label
        self.loudnessThresholdSlider = Scale(self.frame, from_=120, to=1)
        self.loudnessThresholdSlider.grid(row=0, column=1)
        self.loudnessThreshold = tk.Label(self.frame, text="Threshold (dB)", font=self.paramemterFont)
        self.loudnessThreshold.grid(row=1, column=1)

        # Highpass Filter Slider and Label
        self.highPassFilterSlider = Scale(self.frame, from_=1000, to=0)
        self.highPassFilterSlider.grid(row=0, column=2)
        self.highPassFilter = tk.Label(self.frame, text="Highpass (Hz)", font=self.paramemterFont)
        self.highPassFilter.grid(row=1, column=2)

        self.frame.pack(padx=20, pady=10)

        # Decibel Display Frame
        self.dbFrame = tk.Frame(self.root)

        # Configure Grid
        self.dbFrame.columnconfigure(0, weight=1)

        # Label To Display dB Level
        self.decibel = tk.Label(self.dbFrame, text="Loudness (dB): 0", font=("Arial",10))
        self.decibel.grid(row=0, column=0)

        self.dbFrame.pack(pady=5)

        # Button Frame
        self.buttonFrame = tk.Frame(self.root)

        # Configure Button Grid
        self.buttonFrame.columnconfigure(0, weight=1)
        self.buttonFrame.columnconfigure(1, weight=1)

        # Buttons
        self.startButton = tk.Button(self.buttonFrame, text="Start", font=self.buttonFont, command=self.startLoudnessMonitor)
        self.startButton.grid(row=0, column=0, sticky='ew', padx=5)

        self.stopButton = tk.Button(self.buttonFrame, text="Stop", font=self.buttonFont, command=self.stopLoudnessMonitor, state="disabled")
        self.stopButton.grid(row=0, column=1, sticky='ew', padx=5)

        self.buttonFrame.pack(fill='x')

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
            self.updateLoudnessDisplay()
        self.startButton.config(state="disabled")
        self.stopButton.config(state="normal")
        self.volumeSlider.config(state="disabled")
        self.loudnessThresholdSlider.config(state="disabled")
        self.highPassFilterSlider.config(state="disabled")

    # Stop Loudness Monitor
    def stopLoudnessMonitor(self):
        self.loudnessMonitor.stop()
        self.startButton.config(state="normal")
        self.stopButton.config(state="disabled")
        self.volumeSlider.config(state="normal")
        self.loudnessThresholdSlider.config(state="normal")
        self.highPassFilterSlider.config(state="normal")

    # Set saved values (or default if no custom values saved)
    def setValues(self):
        self.highPassFilterSlider.set(200)
        self.loudnessThresholdSlider.set(65)
        self.volumeSlider.set(30)

        #Add saved values

    # Update Decibel Level in GUI
    def updateLoudnessDisplay(self):
        if self.loudnessMonitor.running:
            dB = self.loudnessMonitor.decibel
            self.decibel.config(text=f"Loudness (dB): {max(dB, 0)}")
            self.root.after(100, self.updateLoudnessDisplay)
        else:
            self.decibel.config(text="Loudness (dB): 0")

    # Start GUI
    def startGUI(self):
        self.setValues()
        self.root.geometry("270x215")
        self.root.resizable(False, False)
        self.root.mainloop()

if __name__ == "__main__":
    loudnessMonitor = LoudnessMonitor()
    GUI(loudnessMonitor).startGUI()
