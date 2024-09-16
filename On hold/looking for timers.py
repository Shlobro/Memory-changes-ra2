import psutil
import ctypes
from ctypes import wintypes
import time

# Constants
PROCESS_NAME = "gamemd-spawn.exe"  # Replace with your target process name
BASE_ADDRESS = 0xe91f000
END_ADDRESS = BASE_ADDRESS + 0x86fff0
READ_SIZE = 4096  # Read in chunks of 4 KB
IGNORED_ADDRESSES_FILE = "ignored_addresses.txt"  # Path to the ignored addresses file

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

def find_pid_by_name(name):
    """Find the process ID by its name."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None

def read_process_memory(process_handle, address, size):
    """Read memory from another process."""
    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t()
    result = ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytesRead))
    if result == 0:
        # Check for the specific error code 299 (ERROR_PARTIAL_COPY)
        error_code = ctypes.windll.kernel32.GetLastError()
        if error_code == 299:
            #print(f"Partial read error at {hex(address)}. Skipping this address.")
            return None  # Return None to indicate a failed read due to partial copy
        else:
            raise ctypes.WinError(error_code)
    return buffer.raw

def load_ignored_addresses(file_path):
    """Load ignored addresses from a file."""
    ignored_addresses = set()
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if "absolute address:" in line:
                    # Extract the hexadecimal address after "absolute address:"
                    parts = line.split("absolute address:")
                    address_str = parts[1].split()[0].strip("):")  # Get the address part only and strip unwanted chars
                    abs_address = int(address_str, 16)  # Convert to integer from hex
                    ignored_addresses.add(abs_address)
        print(f"Loaded {len(ignored_addresses)} addresses to ignore.")
    except Exception as e:
        print(f"Failed to load ignored addresses: {e}")
    return ignored_addresses



def monitor_memory():
    ignored_addresses = load_ignored_addresses(IGNORED_ADDRESSES_FILE)
    pid = find_pid_by_name(PROCESS_NAME)
    if pid is None:
        print(f"Could not find process {PROCESS_NAME}")
        return

    process_handle = ctypes.windll.kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not process_handle:
        print("Failed to open process.")
        return

    # Initial memory snapshot
    memory_snapshot = {}

    for address in range(BASE_ADDRESS, END_ADDRESS, READ_SIZE):
        try:
            data = read_process_memory(process_handle, address, READ_SIZE)
            memory_snapshot[address] = data
        except Exception as e:
            print(f"Failed to read memory at {hex(address)}: {e}")

    print("Initial memory snapshot taken. Monitoring for changes...")

    try:
        while True:
            for address in range(BASE_ADDRESS, END_ADDRESS, READ_SIZE):
                try:
                    current_data = read_process_memory(process_handle, address, READ_SIZE)
                    initial_data = memory_snapshot.get(address)
                    if initial_data and current_data != initial_data:
                        for i in range(len(current_data)):
                            if current_data[i] != initial_data[i]:
                                absolute_address = address + i
                                if absolute_address not in ignored_addresses:
                                    offset = address - BASE_ADDRESS + i
                                    print(f"Change detected at offset {hex(offset)} (absolute address: {hex(absolute_address)}): "
                                          f"{hex(initial_data[i])} -> {hex(current_data[i])}")
                                    memory_snapshot[address] = current_data
                except Exception as e:
                    print(f"Failed to read memory at {hex(address)}: {e}")

            time.sleep(1)  # Adjust the sleep time as needed

    finally:
        ctypes.windll.kernel32.CloseHandle(process_handle)

if __name__ == "__main__":
    monitor_memory()
