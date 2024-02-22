import tkinter as tk


class RTLSDR_GUI:
    def __init__(self, root, rtl_sdr_radio):
        self.root = root
        self.rtl_sdr_radio = rtl_sdr_radio

        self.paused = False
        self.squelch = tk.DoubleVar()
        self.squelch.set(self.rtl_sdr_radio.squelch)  # Default squelch value

        self.setup_gui()

    def setup_gui(self):
        # Add a button to pause/resume data acquisition
        self.pause_button = tk.Button(self.root, text="Pause/Resume", command=self.toggle_pause)
        self.pause_button.pack()

        # Add a slider to adjust squelch threshold
        self.squelch_label = tk.Label(self.root, text="Squelch Threshold:")
        self.squelch_label.pack()
        self.squelch_scale = tk.Scale(self.root, from_=-10000, to=10000, orient=tk.HORIZONTAL,
                                      variable=self.squelch, command=self.update_squelch)
        self.squelch_scale.pack()

        # Add a button to apply parameter changes
        self.apply_button = tk.Button(self.root, text="Apply Changes", command=self.apply_parameters)
        self.apply_button.pack()

    def toggle_pause(self):
        # self.paused = not self.paused
        # if self.paused:
        #     self.rtl_sdr_radio.stop()
        # else:
        #     self.rtl_sdr_radio.start()
        pass

    def update_squelch(self, value):
        self.rtl_sdr_radio.squelch = float(value)

    def apply_parameters(self):
        self.paused = False
        self.rtl_sdr_radio.sdr.fc = self.rtl_sdr_radio.freq
        self.rtl_sdr_radio.sdr.err_ppm = self.rtl_sdr_radio.ppm
        self.rtl_sdr_radio.squelch = self.squelch.get()

    def get_squelch_value(self):
        return self.squelch.get()

