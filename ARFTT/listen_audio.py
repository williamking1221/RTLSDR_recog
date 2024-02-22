from typing import List
from rtlsdr import RtlSdr
import argparse
import numpy as np
import pyaudio
import scipy.signal as signal
import matplotlib.pyplot as plt

SampleStream = List[float]
AudioStream = List[int]

stream_buf = bytes()
stream_counter = 0

audio_rate = 48000
audio_output = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=audio_rate, output=True)


def process(samples: SampleStream, sdr: RtlSdr) -> None:
    sample_rate_fm = 240000
    iq_commercial = signal.decimate(samples, int(sdr.get_sample_rate()) // sample_rate_fm)

    angle_commercial = np.unwrap(np.angle(iq_commercial))
    demodulated_commercial = np.diff(angle_commercial)

    audio_signal = signal.decimate(demodulated_commercial, sample_rate_fm // audio_rate, zero_phase=True)
    audio_signal = np.int16(14000 * audio_signal)

    # Apply squelch to the demodulated audio
    squelched_audio = apply_squelch(audio_signal, squelch)

    audio_output.write(squelched_audio.astype("int16").tobytes())


def apply_squelch(audio_signal: np.ndarray, squelch_threshold) -> np.ndarray:
    # Calculate the signal power
    signal_power = np.mean(audio_signal ** 2)

    # If the signal power is below the threshold, set the audio signal to zero
    if signal_power < squelch_threshold:
        squelched_audio = np.zeros_like(audio_signal)
    else:
        squelched_audio = audio_signal

    return squelched_audio


def read_callback(samples, rtl_sdr_obj):
    process(samples, rtl_sdr_obj)


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--ppm', type=int, default=0,
                    help='ppm error correction')
parser.add_argument('--gain', type=int, default=20,
                    help='RF gain level')
parser.add_argument('--freq', type=int, default=147410000,
                    help='frequency to listen to, in Hertz')
parser.add_argument('--squelch', type=float, default=1000,
                    help='minimum threshold required for audio output to show')
parser.add_argument('--verbose', action='store_true',
                    help='mute audio output')

args = parser.parse_args()

sdr = RtlSdr()
sdr.rs = 1024000
sdr.fc = args.freq
sdr.gain = "auto"
sdr.err_ppm = args.ppm
squelch = args.squelch

sdr.read_samples_async(read_callback, int(sdr.get_sample_rate()) // 16)
