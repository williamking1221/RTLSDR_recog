from typing import List
from rtlsdr.rtlsdrtcp.client import RtlSdrTcpClient
import argparse
import numpy as np
import pyaudio
import scipy.signal as signal

SampleStream = List[float]
AudioStream = List[int]

audio_rate = 16000
chunk_size = 1024  # Number of audio samples per chunk
audio_output = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=audio_rate, output=True)

audiobuffer = []


def process(samples: SampleStream, squelch: float) -> List:
    print("Processing")
    sample_rate_fm = 240000
    angle_commercial = np.unwrap(np.angle(samples))
    demodulated_commercial = np.diff(angle_commercial)

    audio_signal = signal.decimate(demodulated_commercial, len(demodulated_commercial) // audio_rate, zero_phase=True)
    audio_signal = np.int16(14000 * audio_signal)

    # Apply squelch to the demodulated audio
    squelched_audio = apply_squelch(audio_signal, squelch)

    # Apply test filter
    filtered_audio = personal_spike_filter(squelched_audio, 5000)

    # Append the filtered audio to the buffer
    audiobuffer.append(filtered_audio)

    # Write chunks of audio data from the buffer to the audio output stream
    while len(audiobuffer) > 0:
        audio_chunk = audiobuffer.pop(0)
        audio_output.write(audio_chunk.astype("int16").tobytes())

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


def personal_spike_filter(signal, magnitude):
    if np.max(signal) > magnitude or np.min(signal) < -magnitude:
        filtered_signal = np.zeros_like(signal)
    else:
        filtered_signal = signal
    return filtered_signal


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--ppm', type=int, default=0,
                        help='ppm error correction')
    parser.add_argument('--gain', type=int, default=20,
                        help='RF gain level')
    parser.add_argument('--freq', type=int, default=147410000,
                        help='frequency to listen to, in Hertz')
    parser.add_argument('--squelch', type=float, default=5000,
                        help='minimum threshold required for audio output to show')
    parser.add_argument('--interval', type=int, default=60, help='transcription interval in seconds')
    parser.add_argument('--verbose', action='store_true',
                        help='mute audio output')

    args = parser.parse_args()

    # Adjust the hostname and port as needed
    sdr = RtlSdrTcpClient(hostname='10.194.89.125', port=1234)
    sdr.rs = 1024000
    sdr.fc = args.freq
    sdr.gain = "auto"
    sdr.err_ppm = args.ppm
    squelch_threshold = args.squelch

    while True:
        data = sdr.read_samples(int(sdr.get_sample_rate()) // 16)
        process(data, squelch_threshold)


if __name__ == "__main__":
    main()
