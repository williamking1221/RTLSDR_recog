import tkinter as tk
from ARFTT.gui import RTLSDR_GUI
from ARFTT.listen_radio import RTLSDR_Radio

# Create the main Tkinter window
root = tk.Tk()
root.title("RTL-SDR Receiver GUI")

# Create an instance of RTLSDR_Radio
freq = 101500000
ppm = 0
squelch = -5000
rtl_sdr_radio = RTLSDR_Radio(freq, ppm, squelch)

# Create an instance of RTLSDR_GUI, passing the RTLSDR_Radio object
rtl_sdr_gui = RTLSDR_GUI(root, rtl_sdr_radio)

# Start the Tkinter main loop
root.mainloop()

