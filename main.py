import tkinter as tk
import asyncio
from ARFTT.gui import RTLSDR_GUI
from ARFTT.listen_radio import RTLSDR_Radio


async def main():
    root = tk.Tk()
    root.title("RTL-SDR Receiver GUI")
    rtl_sdr_radio = RTLSDR_Radio(freq=147410000, ppm=0, squelch=5000, device_index=0)  # Adjust parameters as needed
    rtl_sdr_radio2 = RTLSDR_Radio(freq=147370000, ppm=0, squelch=5000, device_index=1)  # Adjust parameters as needed

    # Create an instance of RTLSDR_GUI, passing the RTLSDR_Radio object
    rtl_sdr_gui = RTLSDR_GUI(root, rtl_sdr_radio, rtl_sdr_radio2)

    while True:
        # Update the Tkinter GUI
        root.update()
        await asyncio.sleep(0.1)  # Allow other tasks to run


# Start the asyncio event loop
asyncio.run(main())
