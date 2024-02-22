from typing import List
from rtlsdr import RtlSdr
from rtlsdr.rtlsdraio import RtlSdrAio
import argparse
import numpy as np
import pyaudio
import scipy.signal as signal


SampleStream = List[float]
AudioStream = List[int]


class RTLSDR_Radio:
    def __init__(self, freq, ppm, squelch):
        self.freq = freq
        self.ppm = ppm
        self.squelch = squelch

        self.audio_rate = 48000
        self.audio_output = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=self.audio_rate, output=True)

    async def process_samples(self, samples: SampleStream, sdr: RtlSdr) -> None:
        sample_rate_fm = 240000
        iq_commercial = signal.decimate(samples, int(self.sdr.get_sample_rate()) // sample_rate_fm)

        angle_commercial = np.unwrap(np.angle(iq_commercial))
        demodulated_commercial = np.diff(angle_commercial)

        audio_signal = signal.decimate(demodulated_commercial, sample_rate_fm // self.audio_rate, zero_phase=True)
        audio_signal = np.int16(14000 * audio_signal)

        # Apply squelch to the demodulated audio
        squelched_audio = self.apply_squelch(audio_signal)

        self.audio_output.write(squelched_audio.astype("int16").tobytes())

    def apply_squelch(self, audio_signal):
        # Calculate the signal power
        signal_power = np.mean(audio_signal ** 2)

        # If the signal power is below the threshold, set the audio signal to zero
        if signal_power < self.squelch:
            squelched_audio = np.zeros_like(audio_signal)
        else:
            squelched_audio = audio_signal

        return squelched_audio

    def read_callback(self, samples, rtl_sdr_obj):
        self.process_samples(samples, rtl_sdr_obj)

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
