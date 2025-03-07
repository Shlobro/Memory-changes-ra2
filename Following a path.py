import ctypes
import psutil
import time
from ctypes import wintypes

KNOWN_OFFSETS = {
    0x0: "GI",
    0x4: "conscript",
    0x8: "tesla trooper",
    0xc: "Allied Engineer",
    0x10: "Rocketeer",
    0x14: "Navy Seal",
    0x18: "Yuri Clone",
    0x1c: "Ivan",
    0x20: "Desolator",
    0x24: "sov dog",
    0x3c: "Chrono legionnaire",
    0x40: "Spy",
    0x50: "Yuri Prime",
    0x54: "Sniper",
    0x60: "Tanya",
    0x6c: "sov engi",
    0x68: "Terrorist",
    0x70: "Allied Dog",
    0xb4: "Yuri Engineer",
    0xb8: "Guardian GI",
    0xbc: "Initiate",
    0xc0: "Boris",
    0xc4: "Brute",
    0xc8: "Virus",
}

IGNORED_OFFSETS = []

MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff
INFANTRYOFFSET = 0x557c  # Offset to get the infantry array pointer
SCAN_SIZE = 0x100  # The size of the memory range we want to scan (4KB)
INT_SIZE = 4  # Size of an integer in bytes


class GameData:
    def __init__(self):
        self.validPlayer = [False] * MAXPLAYERS
        self.infantry_not_allocated = [False] * MAXPLAYERS  # Flag to track if memory not allocated was printed
        self.currentGameRunning = False
        self.memorySnapshot = [None] * MAXPLAYERS  # Changed to one snapshot per player


def find_pid_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None


def read_process_memory(process_handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t()
    try:
        if ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytesRead)):
            return buffer.raw
        else:
            raise ctypes.WinError()
    except OSError as e:
        if e.winerror == 299:  # Only part of a ReadProcessMemory or WriteProcessMemory request was completed
            return None
        else:
            raise


def scan_memory_changes(process_handle, infantry_array_base, prev_snapshot):
    current_snapshot = []
    changes = []

    # Iterate over the range starting from infantry_array_base
    for offset in range(0, SCAN_SIZE, INT_SIZE):
        address = infantry_array_base + offset
        try:
            # Read the current integer value from memory
            current_value_raw = read_process_memory(process_handle, address, INT_SIZE)
            if current_value_raw is None:  # Skip if memory read failed due to WinError 299
                current_snapshot.append(None)
                continue

            current_value = ctypes.c_uint32.from_buffer_copy(current_value_raw).value
            current_snapshot.append(current_value)

            # Skip processing if the offset is in the ignored list
            if offset in IGNORED_OFFSETS:
                continue

            # If this is not the first snapshot, compare with the previous snapshot
            if prev_snapshot is not None:
                prev_value = prev_snapshot[offset // INT_SIZE]
                if prev_value is not None and current_value != prev_value:
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


def read_class_base_mem(game_data):
    pid = find_pid_by_name("gamemd-spawn.exe")
    if pid is None:
        print("Could not find process")
        return

    process_handle = ctypes.windll.kernel32.OpenProcess(
        wintypes.DWORD(0x0010 | 0x0020 | 0x0008 | 0x0010), False, pid)

    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c

    fixedPointValue_raw = read_process_memory(process_handle, fixedPoint, 4)
    if fixedPointValue_raw is None:
        print("Failed to read fixedPoint")
        return
    fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointValue_raw).value

    classBaseArray_raw = read_process_memory(process_handle, classBaseArrayPtr, 4)
    if classBaseArray_raw is None:
        print("Failed to read classBaseArray")
        return
    classBaseArray = ctypes.c_uint32.from_buffer_copy(classBaseArray_raw).value

    # Compute the base pointer for the class base array for all players
    classbasearray = fixedPointValue + 4480

    # A flag to track if any changes were detected during the scan
    any_changes = False

    for i in range(MAXPLAYERS):
        # Store the pointer address used for this player's class pointer
        player_pointer_address = classbasearray
        classBasePtr_raw = read_process_memory(process_handle, player_pointer_address, 4)
        if classBasePtr_raw is None:
            classbasearray += 4
            continue
        classBasePtr = ctypes.c_uint32.from_buffer_copy(classBasePtr_raw).value
        classbasearray += 4

        if classBasePtr != INVALIDCLASS:
            game_data.validPlayer[i] = True
            realClassBasePtr = classBasePtr * 4 + classBaseArray

            realClassBase_raw = read_process_memory(process_handle, realClassBasePtr, 4)
            if realClassBase_raw is None:
                continue
            realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBase_raw).value

            # Get the infantry array pointer using the INFANTRYOFFSET
            infantry_ptr_address = realClassBase + INFANTRYOFFSET
            infantry_array_base_raw = read_process_memory(process_handle, infantry_ptr_address, 4)

            if infantry_array_base_raw is None:
                # Print message only once for this player
                if not game_data.infantry_not_allocated[i]:
                    print(f"Player {i} - No infantry data allocated yet.")
                    game_data.infantry_not_allocated[i] = True
                continue  # Skip this player if infantry data is not allocated yet

            infantry_array_base = ctypes.c_uint32.from_buffer_copy(infantry_array_base_raw).value

            # Initialize or update the memory snapshot for this player
            prev_snapshot = game_data.memorySnapshot[i] if game_data.memorySnapshot[i] is not None else None
            current_snapshot, changes = scan_memory_changes(process_handle, infantry_array_base, prev_snapshot)
            game_data.memorySnapshot[i] = current_snapshot

            # Reset the flag if the memory has been allocated
            game_data.infantry_not_allocated[i] = False

            # Report any changes along with the pointer chain details
            if changes:  # Check if there are any changes for this player
                any_changes = True  # Set the flag if changes were detected
                for change in changes:
                    offset, old_value, new_value, description = change
                    print(f"Player {i} - Memory at offset {hex(offset)}: {old_value} -> {new_value} ({description})")
                    pointer_chain = (
                        f"{hex(player_pointer_address)} -> "
                        f"{hex(classBaseArray)} + {hex(classBasePtr * 4)} = {hex(realClassBasePtr)} -> "
                        f"{hex(realClassBase)} + {hex(INFANTRYOFFSET)} = {hex(infantry_ptr_address)} -> "
                        f"{hex(infantry_array_base)} + {hex(offset)} = {hex(infantry_array_base + offset)}"
                    )
                    print(f"Player {i} - Pointer chain: {pointer_chain}")

    ctypes.windll.kernel32.CloseHandle(process_handle)

    # If any changes occurred during this tick, print a new line
    if any_changes:
        print()  # Print an empty line to separate the changes for each tick


def ra2_main():
    game_data = GameData()

    while True:
        if not find_pid_by_name("gamemd-spawn.exe"):
            game_data.currentGameRunning = False
            time.sleep(1)
            continue

        game_data.currentGameRunning = True
        read_class_base_mem(game_data)
        time.sleep(0.5)


if __name__ == "__main__":
    ra2_main()
