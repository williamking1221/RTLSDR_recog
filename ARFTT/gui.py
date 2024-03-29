import tkinter as tk
import asyncio
from ARFTT.listen_radio import RTLSDR_Radio


class RTLSDR_GUI:
    def __init__(self, root, rtl_sdr_radio):
        self.root = root
        self.root.geometry("400x300")
        self.rtl_sdr_radio = rtl_sdr_radio

        self.paused = True
        self.squelch = tk.DoubleVar()
        self.squelch.set(self.rtl_sdr_radio.squelch)  # Default squelch value
        self.freq_entry_value = tk.StringVar()  # Variable to store frequency input

        self.setup_gui()

    def setup_gui(self):
        # Add a button to pause/resume data acquisition
        self.pause_button = tk.Button(self.root, text="Pause", command=self.toggle_pause)
        self.pause_button.pack()

        self.play_button = tk.Button(self.root, text="Play", command=self.toggle_play)
        self.play_button.pack()

        # Add a slider to adjust squelch threshold
        self.squelch_label = tk.Label(self.root, text="Squelch Threshold:")
        self.squelch_label.pack()
        self.squelch_scale = tk.Scale(self.root, from_=-10000, to=10000, orient=tk.HORIZONTAL,
                                      variable=self.squelch, command=self.update_squelch, length=300)
        self.squelch_scale.pack()

        # Add a label and entry for frequency input
        self.freq_label = tk.Label(self.root, text="Frequency (Hz):")
        self.freq_label.pack()
        self.freq_entry = tk.Entry(self.root)
        self.freq_entry.insert(0, "147410000")  # Default frequency value
        self.freq_entry.pack()

        # Add a button to apply parameter changes
        self.apply_button = tk.Button(self.root, text="Apply Changes", command=self.apply_parameters)
        self.apply_button.pack()

    def toggle_pause(self):
        if not self.paused:
            asyncio.create_task(self.rtl_sdr_radio.stop())
            self.paused = True

    def toggle_play(self):
        if self.paused:
            self.paused = False
            freq = int(self.freq_entry.get())  # Get frequency from entry
            # self.rtl_sdr_radio = RTLSDR_Radio(freq=freq, ppm=0, squelch=self.squelch.get())
            self.rtl_sdr_radio = RTLSDR_Radio(freq=147410000, ppm=0, squelch=self.squelch.get())
            asyncio.create_task(self.rtl_sdr_radio.start())

    def update_squelch(self, value):
        if hasattr(self, 'rtl_sdr_radio'):
            self.rtl_sdr_radio.squelch = float(value)

    def apply_parameters(self):
        self.paused = False
        self.rtl_sdr_radio.sdr.fc = self.rtl_sdr_radio.freq
        self.rtl_sdr_radio.sdr.err_ppm = self.rtl_sdr_radio.ppm
        self.rtl_sdr_radio.squelch = self.squelch.get()

    def get_squelch_value(self):
        return self.squelch.get()
