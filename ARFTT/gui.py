import tkinter as tk
from tkinter import ttk
import asyncio
from ARFTT.listen_radio import RTLSDR_Radio
import json
import queue


def get_color_for_probability(p):
    if p > 0.85:
        return 'great'
    elif 0.70 <= p <= 0.85:
        return 'good'
    elif 0.50 <= p < 0.70:
        return 'average'
    else:
        return 'bad'


class RTLSDR_GUI:
    def __init__(self, root, rtl_sdr_radio, rtl_sdr_radio2=None):
        self.root = root
        self.root.geometry("1600x1200")
        self.rtl_sdr_radio = rtl_sdr_radio
        self.rtl_sdr_radio2 = rtl_sdr_radio2

        # Pass reference to RTLSDR_GUI instance to RTLSDR_Radio
        self.rtl_sdr_radio.gui = self

        self.paused = True
        self.squelch = tk.DoubleVar()
        self.squelch.set(self.rtl_sdr_radio.squelch)  # Default squelch value
        self.freq_entry_value = tk.DoubleVar()  # Variable to store frequency input

        self.paused2 = True
        self.squelch2 = tk.DoubleVar()
        self.squelch2.set(self.rtl_sdr_radio.squelch)  # Default squelch value
        self.freq_entry_value2 = tk.DoubleVar()  # Variable to store frequency input

        self.queue = queue.Queue()
        self.relay_queue = queue.Queue()

        self.queue2 = queue.Queue()
        self.relay_queue2 = queue.Queue()

        self.setup_gui()

        self.root.after(1000, self.process_queue)  # Run every second
        self.root.after(1000, self.process_queue2)  # Run every second
        self.root.after(1000, self.process_relay_queue)  # Run every second
        self.root.after(1000, self.process_relay_queue2)  # Run every second


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
                                      variable=self.squelch, command=lambda value: self.update_squelch(value, dev_num=0),
                                      length=150)
        self.squelch_scale.grid(row=3, column=0, padx=5, pady=5)

        # Create a frame for the buttons
        self.button_frame = ttk.Frame(self.frame1)
        self.button_frame.grid(row=4, column=0, columnspan=2, pady=5)  # Centered under other widgets

        # Pause button
        self.pause_button = tk.Button(self.button_frame, text="Pause", command=self.toggle_pause(0))
        self.pause_button.grid(row=0, column=0, padx=5)

        # Play button
        self.play_button = tk.Button(self.button_frame, text="Play", command=self.toggle_play(0))
        self.play_button.grid(row=0, column=1, padx=5)

        # self.apply_button = tk.Button(self.frame1, text="Apply Changes", command=self.apply_parameters(0))
        # self.apply_button.grid(row=5, column=0, padx=5, pady=5)

        # Transcription Display
        self.transcription_label = tk.Label(self.frame1, text="Transcription:")
        self.transcription_label.grid(row=0, column=2, padx=(0, 250), pady=5, sticky="nsew")

        self.text_display = tk.Text(self.frame1, height=20, width=60, background="black")
        self.text_display.grid(row=1, column=2, rowspan=5, padx=5, pady=5)
        self.text_display.tag_config('neither', foreground="white")
        self.text_display.tag_config('great', foreground="green")
        self.text_display.tag_config('good', foreground="yellow")
        self.text_display.tag_config('average', foreground="orange")
        self.text_display.tag_config('bad', foreground="red")

        self.relay_display = tk.Label(self.frame1, text="Relay Message")
        self.relay_display.grid(row=7, column=2, padx=(0, 250), pady=5, sticky="nsew")

        # Add widgets to frame2 (bottom-left quadrant)
        self.freq_label2 = tk.Label(self.frame2, text="Frequency (Hz):")
        self.freq_label2.grid(row=0, column=0)
        self.freq_entry2 = tk.Entry(self.frame2)
        self.freq_entry2.insert(0, "147370000")  # Default frequency value
        self.freq_entry2.grid(row=1, column=0, padx=5, pady=5)

        self.squelch_label2 = tk.Label(self.frame2, text="Squelch Threshold:")
        self.squelch_label2.grid(row=2, column=0)
        self.squelch_scale2 = tk.Scale(self.frame2, from_=0, to=25000, orient=tk.HORIZONTAL,
                                       variable=self.squelch2, command=lambda value: self.update_squelch(value, dev_num=1),
                                       length=150)
        self.squelch_scale2.grid(row=3, column=0, padx=5, pady=5)

        # Create a frame for the buttons
        self.button_frame2 = ttk.Frame(self.frame2)
        self.button_frame2.grid(row=4, column=0, columnspan=2, pady=5)  # Centered under other widgets

        # Pause button
        self.pause_button2 = tk.Button(self.button_frame2, text="Pause", command=self.toggle_pause(1))
        self.pause_button2.grid(row=0, column=0, padx=5)

        # Play button
        self.play_button2 = tk.Button(self.button_frame2, text="Play", command=self.toggle_play(1))
        self.play_button2.grid(row=0, column=1, padx=5)

        # self.apply_button2 = tk.Button(self.frame2, text="Apply Changes", command=self.apply_parameters(1))
        # self.apply_button2.grid(row=5, column=0, padx=5, pady=5)

        # Transcription Display
        self.transcription_label2 = tk.Label(self.frame2, text="Transcription:")
        self.transcription_label2.grid(row=0, column=2, padx=(0, 250), pady=5, sticky="nsew")

        self.text_display2 = tk.Text(self.frame2, height=20, width=60, background="black")
        self.text_display2.grid(row=1, column=2, rowspan=5, padx=5, pady=5)
        self.text_display2.tag_config('neither', foreground="white")
        self.text_display2.tag_config('great', foreground="green")
        self.text_display2.tag_config('good', foreground="yellow")
        self.text_display2.tag_config('average', foreground="orange")
        self.text_display2.tag_config('bad', foreground="red")

        self.relay_display2 = tk.Label(self.frame2, text="Relay Message")
        self.relay_display2.grid(row=7, column=2, padx=(0, 250), pady=5, sticky="nsew")

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

    def toggle_pause(self, dev_num):
        if dev_num == 0:
            if not self.paused:
                asyncio.create_task(self.rtl_sdr_radio.stop())
                self.paused = True
        elif dev_num == 1:
            if not self.paused2:
                asyncio.create_task(self.rtl_sdr_radio2.stop())
                self.paused2 = True

    def toggle_play(self, dev_num):
        if dev_num == 0:
            if self.paused:
                self.paused = False
                freq = self.freq_entry.get()  # Get frequency from entry
                self.rtl_sdr_radio = RTLSDR_Radio(freq=freq, ppm=0, squelch=self.squelch.get(), device_index=dev_num,
                                                  gui=self)
                asyncio.create_task(self.rtl_sdr_radio.start())
        elif dev_num == 1:
            if self.paused2:
                self.paused2 = False
                freq = self.freq_entry2.get()  # Get frequency from entry
                self.rtl_sdr_radio2 = RTLSDR_Radio(freq=freq, ppm=0, squelch=self.squelch2.get(), device_index=dev_num,
                                                   gui=self)
                asyncio.create_task(self.rtl_sdr_radio2.start())

    def update_squelch(self, value, dev_num):
        if dev_num == 0:
            if hasattr(self, 'rtl_sdr_radio'):
                self.rtl_sdr_radio.squelch = float(value)
        elif dev_num == 1:
            if hasattr(self, 'rtl_sdr_radio2'):
                self.rtl_sdr_radio2.squelch = float(value)

    def apply_parameters(self, dev_num):
        if dev_num == 0:
            freq = int(self.freq_entry.get())  # Get frequency from entry
            self.rtl_sdr_radio.freq = freq
            self.rtl_sdr_radio.sdr.fc = self.rtl_sdr_radio.freq
            self.rtl_sdr_radio.sdr.err_ppm = self.rtl_sdr_radio.ppm
            self.rtl_sdr_radio.squelch = self.squelch.get()
            if self.paused:
                asyncio.create_task(self.rtl_sdr_radio.start())  # Start if paused
        elif dev_num == 1:
            freq = int(self.freq_entry2.get())  # Get frequency from entry
            self.rtl_sdr_radio2.freq = freq
            self.rtl_sdr_radio2.sdr.fc = self.rtl_sdr_radio2.freq
            self.rtl_sdr_radio2.sdr.err_ppm = self.rtl_sdr_radio2.ppm
            self.rtl_sdr_radio2.squelch = self.squelch2.get()
            if self.paused2:
                asyncio.create_task(self.rtl_sdr_radio2.start())  # Start if paused

    def relay_message(self, message, dev_num):
        if dev_num == 0:
            self.relay_queue.put(message)
        elif dev_num == 1:
            self.relay_queue2.put(message)

    def process_relay_queue(self):
        while not self.relay_queue.empty():
            relay_msg = self.relay_queue.get()
            self.relay_display.config(text=relay_msg)
        self.root.after(1000, self.process_relay_queue)

    def process_relay_queue2(self):
        while not self.relay_queue2.empty():
            relay_msg2 = self.relay_queue2.get()
            self.relay_display2.config(text=relay_msg2)
        self.root.after(1000, self.process_relay_queue2)

    def parse_output_json(self, json_file_path, dev_num):
        print(dev_num)
        print(json_file_path)
        if dev_num == 0:
            # Read the JSON file
            with open(json_file_path, 'r') as file:
                json_data = json.load(file)

            # Put the JSON data into the queue
            self.queue.put(json_data)
        elif dev_num == 1:
            # Read the JSON file
            with open(json_file_path, 'r') as file:
                json_data2 = json.load(file)

            # Put the JSON data into the queue
            self.queue2.put(json_data2)

    def process_queue(self):
        while not self.queue.empty():
            # Get the JSON data from the queue
            json_data = self.queue.get()

            self.text_display.delete("1.0", tk.END)

            # Check if translation
            if "params" in json_data:
                self.transcription_label.config(text=f'Spoken Language: {json_data["result"]["language"]}')

            # Extract the transcription text and timestamps from the JSON data
            if "transcription" in json_data:
                for entry in json_data["transcription"]:
                    if "timestamps" in entry and "tokens" in entry:
                        timestamps = entry["timestamps"]
                        self.text_display.insert(tk.END, f"{timestamps['from']} - {timestamps['to']}: ", 'neither')
                        tokens = entry["tokens"]
                        for i in range(len(tokens)):
                            token = tokens[i]
                            token_text = token["text"]
                            if token_text[:2] == "[_":
                                continue
                            else:
                                p = token["p"]
                                status = get_color_for_probability(p)
                                self.text_display.insert(tk.END, token_text, status)
                        self.text_display.insert(tk.END, "\n")  # Insert newline after each transcription entry
        self.root.after(1000, self.process_queue)

    def process_queue2(self):
        while not self.queue2.empty():
            # Get the JSON data from the queue
            json_data2 = self.queue2.get()

            self.text_display2.delete("1.0", tk.END)

            # Check if translation
            if "params" in json_data2:
                self.transcription_label2.config(text=f'Spoken Language: {json_data2["result"]["language"]}')

            # Extract the transcription text and timestamps from the JSON data
            if "transcription" in json_data2:
                for entry in json_data2["transcription"]:
                    if "timestamps" in entry and "tokens" in entry:
                        timestamps = entry["timestamps"]
                        self.text_display2.insert(tk.END, f"{timestamps['from']} - {timestamps['to']}: ", 'neither')
                        tokens = entry["tokens"]
                        for i in range(len(tokens)):
                            token = tokens[i]
                            token_text = token["text"]
                            if token_text[:2] == "[_":
                                continue
                            else:
                                p = token["p"]
                                status = get_color_for_probability(p)
                                self.text_display2.insert(tk.END, token_text, status)
                        self.text_display2.insert(tk.END, "\n")  # Insert newline after each transcription entry
        self.root.after(1000, self.process_queue2)
