from typing import List
from rtlsdr import RtlSdr
import argparse
import numpy as np
import pyaudio
import scipy.signal as signal
import subprocess
import wave
import time
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, medfilt

SampleStream = List[float]
AudioStream = List[int]

stream_buf = bytes()
stream_counter = 0

audio_rate = 16000
audio_output = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=audio_rate, output=True)

audiobuffer = []


def process(samples: SampleStream, sdr: RtlSdr, squelch: float) -> List:
    sample_rate_fm = 240000
    iq_commercial = signal.decimate(samples, int(sdr.get_sample_rate()) // sample_rate_fm)

    angle_commercial = np.unwrap(np.angle(iq_commercial))
    demodulated_commercial = np.diff(angle_commercial)

    audio_signal = signal.decimate(demodulated_commercial, sample_rate_fm // audio_rate, zero_phase=True)
    audio_signal = np.int16(14000 * audio_signal)

    # Apply squelch to the demodulated audio
    squelched_audio = apply_squelch(audio_signal, squelch)

    # Apply low-pass filter to the audio signal
    # filtered_audio = lowpass_filter(squelched_audio, cutoff_freq=5000, sampling_freq=audio_rate)

    # Apply median filter to remove large spikes
    # filtered_audio = remove_large_spikes(squelched_audio, window_size=101)

    # Apply test filter
    filtered_audio = personal_spike_filter(squelched_audio, 5000)

    audio_output.write(filtered_audio.astype("int16").tobytes())

    audiobuffer.append(filtered_audio)

    # Check if it's time to plot (every 30 seconds)
    if len(audiobuffer) * 1024 / audio_rate >= 30:
        plot_audio()

    return filtered_audio


def apply_squelch(audio_signal: np.ndarray, squelch_threshold) -> np.ndarray:
    # Calculate the signal power
    signal_power = np.mean(audio_signal ** 2)

    # If the signal power is below the threshold, set the audio signal to zero
    if signal_power < squelch_threshold:
        squelched_audio = np.zeros_like(audio_signal)
    else:
        squelched_audio = audio_signal

    return squelched_audio


def lowpass_filter(signal, cutoff_freq, sampling_freq):
    nyquist_freq = 0.5 * sampling_freq
    normalized_cutoff = cutoff_freq / nyquist_freq
    b, a = butter(1, normalized_cutoff, btype='low', analog=False)  # Using a first-order Butterworth filter for simplicity
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal


def remove_large_spikes(signal, window_size):
    filtered_signal = medfilt(signal, kernel_size=window_size)
    return filtered_signal


def personal_spike_filter(signal, magnitude):
    if np.max(signal) > magnitude or np.min(signal) < -magnitude:
        filtered_signal = np.zeros_like(signal)
    else:
        filtered_signal = signal
    return filtered_signal


def transcribe_audio(full_audio: np.ndarray):
    # Save audio to a WAV file
    filename = f"audio_{int(time.time())}.wav"
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(audio_rate)
        wf.writeframes(full_audio.tobytes())

    # Call transcription command
    subprocess.run(["../whisper.cpp/main", "-m", "../whisper.cpp/models/ggml-base.en.bin", "-f", filename])


def plot_audio():
    full_audio = np.concatenate(audiobuffer)
    print(full_audio.shape)

    # Clear the audio buffer
    audiobuffer.clear()

    # Plot the squelched audio
    plt.figure()
    plt.plot(full_audio)
    plt.title('Squelched Audio')
    plt.xlabel('Sample')
    plt.ylabel('Amplitude')
    plt.show()


def read_callback(samples, rtl_sdr_obj):
    process(samples, rtl_sdr_obj, 1000)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--ppm', type=int, default=0,
                        help='ppm error correction')
    parser.add_argument('--gain', type=int, default=20,
                        help='RF gain level')
    parser.add_argument('--freq', type=int, default=147410000,
                        help='frequency to listen to, in Hertz')
    parser.add_argument('--squelch', type=float, default=1000,
                        help='minimum threshold required for audio output to show')
    parser.add_argument('--interval', type=int, default=60, help='transcription interval in seconds')
    parser.add_argument('--verbose', action='store_true',
                        help='mute audio output')

    args = parser.parse_args()

    sdr = RtlSdr()
    sdr.rs = 1024000
    sdr.fc = args.freq
    sdr.gain = "auto"
    sdr.err_ppm = args.ppm
    squelch_threshold = args.squelch
    transcription_interval = args.interval

    sdr.read_samples_async(read_callback, int(sdr.get_sample_rate()) // 16)


if __name__ == "__main__":
    main()
