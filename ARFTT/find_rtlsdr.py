from rtlsdr import RtlSdr

# Get a list of detected device serial numbers (str)
serial_numbers = RtlSdr.get_device_serial_addresses()

if __name__ == "__main__":
    print(serial_numbers)
    print(RtlSdr.get_device_index_by_serial('00000001'))
    print(RtlSdr.get_device_index_by_serial('00000002'))
