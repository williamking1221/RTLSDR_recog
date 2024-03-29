from typing import List
from rtlsdr import RtlSdr
import argparse
import numpy as np
import pyaudio
import scipy.signal as signal
import subprocess

SampleStream = List[float]
AudioStream = List[int]

stream_buf = bytes()
stream_counter = 0

audio_rate = 48000
audio_output = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=audio_rate, output=True)


def process(samples: SampleStream, sdr: RtlSdr, squelch: float) -> None:
    sample_rate_fm = 240000
    iq_commercial = signal.decimate(samples, int(sdr.get_sample_rate()) // sample_rate_fm)

    angle_commercial = np.unwrap(np.angle(iq_commercial))
    demodulated_commercial = np.diff(angle_commercial)

    audio_signal = signal.decimate(demodulated_commercial, sample_rate_fm // audio_rate, zero_phase=True)
    audio_signal = np.int16(14000 * audio_signal)

    # Apply squelch to the demodulated audio
    squelched_audio = apply_squelch(audio_signal, squelch)

    # audio_output.write(squelched_audio.astype("int16").tobytes())
    return squelched_audio


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
    parser.add_argument('--verbose', action='store_true',
                        help='mute audio output')

    args = parser.parse_args()

    sdr = RtlSdr()
    sdr.rs = 1024000
    sdr.fc = args.freq
    sdr.gain = "auto"
    sdr.err_ppm = args.ppm
    squelch_threshold = args.squelch

    # Start the subprocess for whisper.cpp
    whisper_command = ["../whisper.cpp/stream", "-m", "../whisper.cpp/models/ggml-base.en.bin", "-t", "8", "--step",
                       "500", "--length", "5000"]
    whisper_process = subprocess.Popen(whisper_command, stdin=subprocess.PIPE)

    print("Streaming audio to whisper.cpp. Press Ctrl+C to stop.")

    # sdr.read_samples_async(read_callback, int(sdr.get_sample_rate()) // 16)

    try:
        while True:
            # Read samples from RTL-SDR
            samples = sdr.read_samples(1024)

            # Process samples and apply squelch
            sq_audio = process(samples, sdr, squelch_threshold)

            # Write audio data to whisper.cpp process stdin
            whisper_process.stdin.write(sq_audio.tobytes())

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        # Clean up resources
        sdr.close()
        whisper_process.terminate()


if __name__ == "__main__":
    main()
