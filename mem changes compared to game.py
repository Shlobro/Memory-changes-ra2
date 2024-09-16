import ctypes
from ctypes import wintypes
import psutil
import time

# Keep relevant known offsets for global game data
KNOWN_OFFSETS = {
    0x53a4: "Power output",
    0x53a8: "Power drain",
    0x5538: "Infantry count",
    0x5588: "Infantry count",
    0x55b0: "Total amount of structures placed",
    0x53e4: "Infantry lost",
    # More global game-state offsets here...
}

IGNORED_OFFSETS = [0x30c, 0x2dc, 0x57a4]  # Adjusted as needed

# Set scan size and other parameters
SCAN_SIZE = 0x10000
START_OFFSET = 0x0  # Adjust if needed
INT_SIZE = 4  # Size of an integer in bytes

class GameData:
    def __init__(self):
        self.memorySnapshot = [None] * SCAN_SIZE  # Snapshot for global game data


def find_pid_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None


def read_process_memory(process_handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t()
    if ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytesRead)):
        return buffer.raw
    else:
        raise ctypes.WinError()


def scan_memory_changes(process_handle, base_address, prev_snapshot):
    current_snapshot = []
    changes = []

    # Iterate over the memory space, starting at base_address + START_OFFSET
    for offset in range(START_OFFSET, START_OFFSET + SCAN_SIZE, INT_SIZE):
        address = base_address + offset
        try:
            # Read the current integer value from memory
            current_value = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, address, INT_SIZE)).value
            current_snapshot.append(current_value)

            # Skip processing if the offset is in the ignored list
            if offset in IGNORED_OFFSETS:
                continue

            # If this is not the first snapshot, compare with the previous snapshot
            if prev_snapshot is not None:
                prev_value = prev_snapshot[(offset - START_OFFSET) // INT_SIZE]
                if current_value != prev_value:
                    # A change is detected, record the change
                    description = KNOWN_OFFSETS.get(offset, None)
                    if description:
                        changes.append((offset, prev_value, current_value, description))
                    else:
                        changes.append((offset, prev_value, current_value, "Unknown offset"))

        except Exception as e:
            # Handle cases where memory could not be read
            print(f"Failed to read memory at address {hex(address)}: {e}")
            current_snapshot.append(None)

    return current_snapshot, changes


def read_game_base_mem(game_data):
    pid = find_pid_by_name("gamemd-spawn.exe")
    if pid is None:
        print("Could not find process")
        return

    process_handle = ctypes.windll.kernel32.OpenProcess(
        wintypes.DWORD(0x0010 | 0x0020 | 0x0008 | 0x0010), False, pid)

    # Assuming 0xA8B230 is the game's base address. Adjust if necessary.
    game_base_address = 0xa8b230

    # Read the base address
    base_address_value = ctypes.c_uint32.from_buffer_copy(read_process_memory(process_handle, game_base_address, 4)).value

    # Scan global memory state starting from the base address
    prev_snapshot = game_data.memorySnapshot
    current_snapshot, changes = scan_memory_changes(process_handle, base_address_value, prev_snapshot)
    game_data.memorySnapshot = current_snapshot

    # Report any changes
    if changes:
        for change in changes:
            offset, old_value, new_value, description = change
            print(f"Memory at offset {hex(offset)}: {old_value} -> {new_value} ({description})")

    ctypes.windll.kernel32.CloseHandle(process_handle)


def ra2_main():
    game_data = GameData()

    while True:
        if not find_pid_by_name("gamemd-spawn.exe"):
            time.sleep(1)
            continue

        read_game_base_mem(game_data)
        time.sleep(0.5)


if __name__ == "__main__":
    ra2_main()
