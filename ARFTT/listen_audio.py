import argparse
import pyaudio
import threading
from rtlsdr import RtlSdr

AudioStream = bytes

stream_buf = bytes()
stream_counter = 0

audio_rate = 48000

audio_output = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=audio_rate, output=True)


def stream_audio(data: AudioStream):
    global stream_buf
    global stream_counter

    audio_output.write(data)


def read_callback(samples, rtl_sdr_obj):
    # Directly stream the received samples to audio output
    stream_audio(samples.tobytes())


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--ppm', type=int, default=0,
                    help='ppm error correction')
parser.add_argument('--gain', type=int, default=20,
                    help='RF gain level')
parser.add_argument('--freq', type=int, default=92900000,
                    help='frequency to listen to, in Hertz')

args = parser.parse_args()

sdr = RtlSdr()
sdr.rs = 2400000
sdr.fc = args.freq
sdr.gain = args.gain
sdr.err_ppm = args.ppm

sdr.read_samples_async(read_callback, int(sdr.get_sample_rate()) // 16)
