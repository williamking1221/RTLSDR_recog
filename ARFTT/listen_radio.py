from typing import List, Callable, Any
from rtlsdr import RtlSdr
from rtlsdr.rtlsdraio import RtlSdrAio
import numpy as np
import pyaudio
import scipy.signal as signal
import subprocess
import threading
import wave
import time
import os
import matplotlib.pyplot as plt


SampleStream = List[float]
AudioStream = List[int]


class RTLSDR_Radio:
    def __init__(self, freq, ppm, squelch, gui=None, output_callback: Callable[[str], Any] = None):
        self.freq = freq
        self.ppm = ppm
        self.squelch = squelch
        self.gui = gui

        self.audio_rate = 16000
        self.audio_output = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=self.audio_rate, output=True)

        self.audio_buffer = []  # Initialize audio buffer to store segments
        self.transcribe_interval = 30  # Interval for transcription check in seconds

        # Start a separate thread for transcription
        self.transcribe_thread = threading.Thread(target=self.transcribe_audio_thread, daemon=True)
        self.transcribe_thread.start()

    async def process_samples(self, samples: SampleStream, sdr: RtlSdr) -> None:
        sample_rate_fm = 240000
        iq_commercial = signal.decimate(samples, int(self.sdr.get_sample_rate()) // sample_rate_fm)

        angle_commercial = np.unwrap(np.angle(iq_commercial))
        demodulated_commercial = np.diff(angle_commercial)

        audio_signal = signal.decimate(demodulated_commercial, sample_rate_fm // self.audio_rate, zero_phase=True)
        audio_signal = np.int16(14000 * audio_signal)

        filtered_audio = self.personal_spike_filter(audio_signal)

        self.audio_output.write(filtered_audio.astype("int16").tobytes())

        self.audio_buffer.append(filtered_audio)

    def apply_squelch(self, audio_signal):
        # Calculate the signal power
        signal_power = np.mean(audio_signal ** 2)

        # If the signal power is below the threshold, set the audio signal to zero
        if signal_power < self.squelch:
            squelched_audio = np.zeros_like(audio_signal)
        else:
            squelched_audio = audio_signal

        return squelched_audio

    def personal_spike_filter(self, audio_signal):
        if np.max(audio_signal) > self.squelch or np.min(audio_signal) < -self.squelch:
            filtered_signal = np.zeros_like(audio_signal)
        else:
            filtered_signal = audio_signal
        return filtered_signal

    def transcribe_audio_thread(self):
        while True:
            # Check if there's enough audio to transcribe
            if len(self.audio_buffer) == 0:
                if self.gui is not None:
                    self.gui.relay_message(f"Silence at {self.freq}")
                time.sleep(self.transcribe_interval)  # Sleep for a short duration and check again
                continue

            # Concatenate audio segments
            full_audio = np.concatenate(self.audio_buffer)

            # If there is speech in the approximately last 15 seconds, don't cut yet.
            if np.max(full_audio[-250000:]) > 0:
                if self.gui is not None:
                    self.gui.relay_message(f"Audio at {self.freq}")
                time.sleep(self.transcribe_interval)
                continue

            # Remove trailing zeros
            nonzero_indices = np.nonzero(full_audio)[0]
            if len(nonzero_indices) > 0:
                if self.gui is not None:
                    self.gui.relay_message(f"Processing Audio at {self.freq}")
                first_nonzero_idx = nonzero_indices[0]
                print(first_nonzero_idx)
                last_nonzero_idx = nonzero_indices[-1]
                print(last_nonzero_idx)
                full_audio = full_audio[first_nonzero_idx:last_nonzero_idx]
                self.audio_buffer.clear()

                # Save concatenated audio to a WAV file
                curr_time = int(time.time())
                filename = f"audio_{curr_time}.wav"
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.audio_rate)
                    wf.writeframes(full_audio.tobytes())

                # Call transcription command
                subprocess.run(["whisper.cpp/main", "-m", "whisper.cpp/models/ggml-medium.bin","-pc", "-tr", "-ojf",
                                "-l", "auto", "-f", filename])

                json_file_path = f"audio_{curr_time}.wav.json"
                if self.gui is not None:
                    if os.path.exists(json_file_path):
                        self.gui.parse_output_json(json_file_path)

                # Sleep for the remaining time until the next transcription interval
                time.sleep(self.transcribe_interval)
            else:
                if self.gui is not None:
                    self.gui.relay_message(f"Silence at {self.freq}")
                    self.audio_buffer.clear()
                    time.sleep(self.transcribe_interval)

    async def start(self):
        self.sdr = RtlSdrAio()
        self.sdr.rs = 1024000
        self.sdr.fc = self.freq
        self.sdr.gain = "auto"
        self.sdr.err_ppm = self.ppm

        async for samples in self.sdr.stream():
            await self.process_samples(samples, self.sdr)

    async def stop(self):
        await self.sdr.stop()
