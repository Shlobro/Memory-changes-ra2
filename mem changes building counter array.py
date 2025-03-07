import ctypes
import psutil
import time
from ctypes import wintypes

KNOWN_OFFSETS = {
    0x0: "Allied Power Plant",
    0x4: "Allied Ore Refinery",
    0x8: "Allied Con Yard",
    0xc: "Allied Barracks",
    0x14: "Allied service Depot",
    0x18: "Allied Battle Lab",
    0x1c: "Allied War Factory",
    0x24: "tesla reactor",
    0x28: "Sov Battle lab",
    0x2c: "sov barracks",
    0x34: "Sov Radar",
    0x38: "Sov War Factory",
    0x3c: "Sov Ore Ref",
    0x48: "Yuri Radar",
    0x50: "Sentry Gun",
    0x54: "Patriot Missile",
    0x5c: "Allied Naval Yard",
    0x60: "Iron Curtain",
    0x64: "sov con yard",
    0x68: "Sov Service Depot",
    0x6c: "Chrono Sphere",
    0x74: "Weather Controller",
    0xd4: "Tesla Coil",
    0xd8: "Nuclear Missile Launcher",
    0xf4: "Sov Naval Yard",
    0xf8: "SpySat Uplink",
    0xfc: "Gap Generator",
    0x100: "Grand Cannon",
    0x104: "Nuclear Reactor",
    0x108: "PillBox",
    0x10c: "Flak Cannon",
    0x11c: "Oil",
    0x120: "Cloning Vats",
    0x124: "Ore Purifier",
    0x1a4: "Allied AFC",
    0x21c: "American AFC",
0x2dc: "Blitz oil (psychic sensor)",
    0x4b0: "Yuri Con Yard",
    0x4b4: "Bio Reactor",
    0x4b8: "Yuri Barracks",
    0x4bc: "Yuri War Factory",
    0x4c0: "Yuri Naval Yard",
    0x4c8: "Yuri Battle Lab",
    0x4d0: "Gattling Cannon",
    0x4d4: "Psychic Tower",
    0x4d8: "Industrial Plant",
    0x4dc: "Grinder",
    0x4e0: "Genetic Mutator",
    0x4ec: "Psychic dominator",
    0x558: "Tank Bunker",
    0x590: "Robot Control Center",
    0x594: "Slave Miner Deployed",
    0x59c: "Battle Bunker",

}

IGNORED_OFFSETS = []

MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff
BUILDINGOFFSET = 0x5554  # Offset to get the building array pointer
SCAN_SIZE = 0x600  # The size of the memory range we want to scan (4KB)
INT_SIZE = 4  # Size of an integer in bytes


class GameData:
    def __init__(self):
        self.validPlayer = [False] * MAXPLAYERS
        self.building_not_allocated = [False] * MAXPLAYERS  # Flag to track if memory not allocated was printed
        self.currentGameRunning = False
        self.memorySnapshot = [None] * SCAN_SIZE


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


def scan_memory_changes(process_handle, building_array_base, prev_snapshot):
    current_snapshot = []
    changes = []

    # Iterate over the range starting from building_array_base
    for offset in range(0, SCAN_SIZE, INT_SIZE):
        address = building_array_base + offset
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

    fixedPointValue = ctypes.c_uint32.from_buffer_copy(read_process_memory(process_handle, fixedPoint, 4)).value
    classBaseArray = ctypes.c_uint32.from_buffer_copy(read_process_memory(process_handle, classBaseArrayPtr, 4)).value

    classbasearray = fixedPointValue + 1120 * 4

    # A flag to track if any changes were detected during the scan
    any_changes = False

    for i in range(MAXPLAYERS):
        classBasePtr = ctypes.c_uint32.from_buffer_copy(read_process_memory(process_handle, classbasearray, 4)).value
        classbasearray += 4
        if classBasePtr != INVALIDCLASS:
            game_data.validPlayer[i] = True
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBase = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, realClassBasePtr, 4)).value

            # Get the building array pointer using the BUILDINGOFFSET
            building_ptr_address = realClassBase + BUILDINGOFFSET
            building_array_base_raw = read_process_memory(process_handle, building_ptr_address, 4)

            if building_array_base_raw is None:
                # Print message only once for this player
                if not game_data.building_not_allocated[i]:
                    print(f"Player {i} - No building data allocated yet.")
                    game_data.building_not_allocated[i] = True
                continue  # Skip this player if building data is not allocated yet

            building_array_base = ctypes.c_uint32.from_buffer_copy(building_array_base_raw).value

            # Initialize or update the memory snapshot
            prev_snapshot = game_data.memorySnapshot[i] if game_data.memorySnapshot[i] is not None else None
            current_snapshot, changes = scan_memory_changes(process_handle, building_array_base, prev_snapshot)
            game_data.memorySnapshot[i] = current_snapshot

            # Reset the flag if the memory has been allocated
            game_data.building_not_allocated[i] = False

            # Report any changes
            if changes:  # Check if there are any changes for this player
                any_changes = True  # Set the flag if changes were detected
                for change in changes:
                    offset, old_value, new_value, description = change
                    print(f"Player {i} - Memory at offset {hex(offset)}: {old_value} -> {new_value} ({description})")

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
