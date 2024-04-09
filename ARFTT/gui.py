import tkinter as tk
from tkinter import ttk
import asyncio
from ARFTT.listen_radio import RTLSDR_Radio

class RTLSDR_GUI:
    def __init__(self, root, rtl_sdr_radio):
        self.root = root
        self.root.geometry("1200x1200")
        self.rtl_sdr_radio = rtl_sdr_radio

        self.paused = True
        self.squelch = tk.DoubleVar()
        self.squelch.set(self.rtl_sdr_radio.squelch)  # Default squelch value
        self.freq_entry_value = tk.DoubleVar()  # Variable to store frequency input

        self.setup_gui()

    def setup_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text='Friendly')
        self.notebook.add(self.tab2, text='Enemy')

        self.setup_friendly()
        # Tab 2 is blank, no setup needed

    def setup_friendly(self):
        # Create four frames for quadrants
        self.frame1 = ttk.Frame(self.tab1)
        self.frame1.grid(row=0, column=0, sticky="nsew")
        self.frame2 = ttk.Frame(self.tab1)
        self.frame2.grid(row=0, column=1, sticky="nsew")
        self.frame3 = ttk.Frame(self.tab1)
        self.frame3.grid(row=1, column=0, sticky="nsew")
        self.frame4 = ttk.Frame(self.tab1)
        self.frame4.grid(row=1, column=1, sticky="nsew")

        # Add widgets to frame1 (top-left quadrant)
        self.freq_label = tk.Label(self.frame1, text="Frequency (Hz):")
        self.freq_label.grid(row=0, column=0)
        self.freq_entry = tk.Entry(self.frame1)
        self.freq_entry.insert(0, "147410000")  # Default frequency value
        self.freq_entry.grid(row=1, column=0, padx=5, pady=5)

        self.squelch_label = tk.Label(self.frame1, text="Squelch Threshold:")
        self.squelch_label.grid(row=2, column=0)
        self.squelch_scale = tk.Scale(self.frame1, from_=0, to=25000, orient=tk.HORIZONTAL,
                                    variable=self.squelch, command=self.update_squelch, length=150)
        self.squelch_scale.grid(row=3, column=0, padx=5, pady=5)

        # Create a frame for the buttons
        self.button_frame = ttk.Frame(self.frame1)
        self.button_frame.grid(row=4, column=0, columnspan=2, pady=5)  # Centered under other widgets
        
        # Pause button
        self.pause_button = tk.Button(self.button_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.grid(row=0, column=0, padx=5) 

        # Play button
        self.play_button = tk.Button(self.button_frame, text="Play", command=self.toggle_play)
        self.play_button.grid(row=0, column=1, padx=5)  

        self.apply_button = tk.Button(self.frame1, text="Apply Changes", command=self.apply_parameters)
        self.apply_button.grid(row=5, column=0, padx=5, pady=5)

        # Transcription Display
        self.transcription_label = tk.Label(self.frame1, text="Transcription:")
        self.transcription_label.grid(row=0, column=2, padx=(0,250), pady=5, sticky="nsew") 

        self.text_display = tk.Text(self.frame1, height=10, width=40)
        self.text_display.grid(row=1, column=2, rowspan=5, padx=5, pady=5)

        # Add widgets to frame2 (bottom-left quadrant)
        self.freq_label2 = tk.Label(self.frame2, text="Frequency (Hz):")
        self.freq_label2.grid(row=0, column=0)
        self.freq_entry2 = tk.Entry(self.frame2)
        self.freq_entry2.insert(0, "222220000")  # Default frequency value
        self.freq_entry2.grid(row=1, column=0, padx=5, pady=5)

        # Add widgets to frame3 (bottom-left quadrant)
        self.freq_label3 = tk.Label(self.frame3, text="Frequency (Hz):")
        self.freq_label3.grid(row=0, column=0)
        self.freq_entry3 = tk.Entry(self.frame3)
        self.freq_entry3.insert(0, "333330000")  # Default frequency value
        self.freq_entry3.grid(row=1, column=0, padx=5, pady=5)

        # Add widgets to frame4 (bottom-left quadrant)
        self.freq_label4 = tk.Label(self.frame4, text="Frequency (Hz):")
        self.freq_label4.grid(row=0, column=0)
        self.freq_entry4 = tk.Entry(self.frame4)
        self.freq_entry4.insert(0, "444440000")  # Default frequency value
        self.freq_entry4.grid(row=1, column=0, padx=5, pady=5)


    def toggle_pause(self):
        if not self.paused:
            asyncio.create_task(self.rtl_sdr_radio.stop())
            self.paused = True

    def toggle_play(self):
        if self.paused:
            self.paused = False
            freq = self.freq_entry.get()  # Get frequency from entry
            # self.rtl_sdr_radio = RTLSDR_Radio(freq=freq, ppm=0, squelch=self.squelch.get())
            self.rtl_sdr_radio = RTLSDR_Radio(freq=freq, ppm=0, squelch=self.squelch.get())
            # self.rtl_sdr_radio = RTLSDR_Radio(freq=105100000, ppm=0, squelch=self.squelch.get())
            asyncio.create_task(self.rtl_sdr_radio.start())

    def update_squelch(self, value):
        if hasattr(self, 'rtl_sdr_radio'):
            self.rtl_sdr_radio.squelch = float(value)

    def apply_parameters(self):
        freq = int(self.freq_entry.get())  # Get frequency from entry
        self.rtl_sdr_radio.freq = freq
        self.rtl_sdr_radio.sdr.fc = self.rtl_sdr_radio.freq
        self.rtl_sdr_radio.sdr.err_ppm = self.rtl_sdr_radio.ppm
        self.rtl_sdr_radio.squelch = self.squelch.get()
        if self.paused:
            asyncio.create_task(self.rtl_sdr_radio.start())  # Start if paused

if __name__ == "__main__":
    root = tk.Tk()
    rtl_sdr_radio = RTLSDR_Radio(freq=147410000, ppm=0, squelch=10000)
    gui = RTLSDR_GUI(root, rtl_sdr_radio)
    root.mainloop()
