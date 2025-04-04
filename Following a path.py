import ctypes
import psutil
import time
from ctypes import wintypes

# Global constants and offsets
MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff

# Base offset from player base for infantry factory
INFANTRYFACTORYOFFSET = 0x53b0

# Offsets inside FactoryClass
PERCENTAGECOMPLETEOFFSET = 0x24    # Percentage complete of the unit being built
QUEUEDUNITSAMOUNT = 0x50           # Number of queued units (not used for Buildings)
QUEUEDUNITSPTROFFSET = 0x44        # Pointer to queued units array (not used for Buildings)

# Offsets inside technoTypeClass
UNITNAMEOFFSET = 0x64             # Offset to read 20 bytes string for unit name

# Offsets in technoClass to get to technoType pointer.
TECHNOCLASS_TO_TECHNOTYPE_INFANTRY_OFFSET = 0x6c0  # For Infantry factories
TECHNOCLASS_TO_TECHNOTYPE_BUILDINGS_OFFSET = 0x520 # For Buildings factories
TECHNOCLASS_TO_TECHNOTYPE_UNIT_OFFSET = 0x6c4        # For Tanks, Aircraft, Ships, and Defenses

# Global factory type offsets relative to INFANTRYFACTORYOFFSET
AIRCRAFT_FACTORY_OFFSET = INFANTRYFACTORYOFFSET - 4
INFANTRY_FACTORY_OFFSET = INFANTRYFACTORYOFFSET
VEHICLES_FACTORY_OFFSET = INFANTRYFACTORYOFFSET + 4
SHIPS_FACTORY_OFFSET = INFANTRYFACTORYOFFSET + 8
BUILDINGS_FACTORY_OFFSET = INFANTRYFACTORYOFFSET + 12
DEFENSES_FACTORY_OFFSET = INFANTRYFACTORYOFFSET + 28

# Global list of factory types (name, offset)
FACTORIES = [
    ("Aircraft", AIRCRAFT_FACTORY_OFFSET),
    ("Infantry", INFANTRY_FACTORY_OFFSET),
    ("Vehicles", VEHICLES_FACTORY_OFFSET),
    ("Ships", SHIPS_FACTORY_OFFSET),
    ("Buildings", BUILDINGS_FACTORY_OFFSET),
    ("Defenses", DEFENSES_FACTORY_OFFSET),
]

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
        if e.winerror == 299:  # Partial read; return None
            return None
        else:
            raise

def get_unit_name_from_techno_type(techno_type_ptr, process_handle, player_number):
    """
    Given a pointer to a technoTypeClass, add UNITNAMEOFFSET and read 20 bytes for the unit name.
    """
    string_address = techno_type_ptr + UNITNAMEOFFSET
    string_data = read_process_memory(process_handle, string_address, 20)
    if string_data is None:
        return False
    techno_string = string_data.split(b'\x00')[0].decode('utf-8', errors='replace')
    return techno_string

def get_unit_name_from_techno_class(techno_class_ptr, process_handle, player_number, techno_offset):
    """
    Given a pointer to a technoClass, add the given techno_offset to get the technoType pointer,
    then return the unit name from that technoType pointer.
    """
    techno_type_ptr_address = techno_class_ptr + techno_offset
    techno_type_ptr_data = read_process_memory(process_handle, techno_type_ptr_address, 4)
    if techno_type_ptr_data is None:
        return False
    techno_type_ptr = ctypes.c_uint32.from_buffer_copy(techno_type_ptr_data).value
    return get_unit_name_from_techno_type(techno_type_ptr, process_handle, player_number)

def process_factory(realClassBase, process_handle, player_number, factory_offset, factory_name):
    """
    Process a single factory.
    For Buildings, no queued unit information is processed.
    For other factories, if the factory pointer is allocated and active (nonzero progress or queue),
    prints the percentage complete, current unit being built, and queued units.
    """
    factory_ptr_address = realClassBase + factory_offset
    factory_ptr_data = read_process_memory(process_handle, factory_ptr_address, 4)
    if factory_ptr_data is None:
        return  # Factory pointer not allocated.
    factory_ptr = ctypes.c_uint32.from_buffer_copy(factory_ptr_data).value
    if factory_ptr == 0:
        return

    # Read percentage complete from FactoryClass.
    percentage_data = read_process_memory(process_handle, factory_ptr + PERCENTAGECOMPLETEOFFSET, 4)
    if percentage_data is None:
        return
    percentage_val = ctypes.c_uint32.from_buffer_copy(percentage_data).value
    percentage_val = 100 / 54 * percentage_val

    # For factories other than Buildings, read the queued units amount.
    queued_units_val = 0
    if factory_name != "Buildings":
        queued_units_data = read_process_memory(process_handle, factory_ptr + QUEUEDUNITSAMOUNT, 4)
        if queued_units_data is None:
            return
        queued_units_val = ctypes.c_uint32.from_buffer_copy(queued_units_data).value

    # If nothing is being built (no progress and no queued units for non-buildings), skip output.
    if percentage_val == 0 and queued_units_val == 0:
        return

    print(f"Player {player_number} ({factory_name}): Complete: {percentage_val}")

    if factory_name != "Buildings":
        print(f"Player {player_number} ({factory_name}): Queued amount: {queued_units_val}")

    # Read the technoClass pointer from FactoryClass (offset 0x58)
    techno_class_ptr_address = factory_ptr + 0x58
    techno_class_ptr_data = read_process_memory(process_handle, techno_class_ptr_address, 4)
    if techno_class_ptr_data is None:
        return
    techno_class_ptr = ctypes.c_uint32.from_buffer_copy(techno_class_ptr_data).value

    # Choose the appropriate offset based on the factory type.
    if factory_name == "Buildings":
        techno_offset = TECHNOCLASS_TO_TECHNOTYPE_BUILDINGS_OFFSET
    elif factory_name == "Infantry":
        techno_offset = TECHNOCLASS_TO_TECHNOTYPE_INFANTRY_OFFSET
    elif factory_name in ("Aircraft", "Vehicles", "Ships", "Defenses"):
        techno_offset = TECHNOCLASS_TO_TECHNOTYPE_UNIT_OFFSET
    else:
        techno_offset = TECHNOCLASS_TO_TECHNOTYPE_UNIT_OFFSET

    unit_name = get_unit_name_from_techno_class(techno_class_ptr, process_handle, player_number, techno_offset)
    if not unit_name:
        return
    print(f"Player {player_number} ({factory_name}) is building: {unit_name}")

    # Process queued units only if this factory is not Buildings.
    if factory_name != "Buildings":
        queued_units_ptr_address = factory_ptr + QUEUEDUNITSPTROFFSET
        queued_units_ptr_data = read_process_memory(process_handle, queued_units_ptr_address, 4)
        if queued_units_ptr_data is None:
            return
        queued_units_ptr = ctypes.c_uint32.from_buffer_copy(queued_units_ptr_data).value
        queued_units_list = []
        for j in range(queued_units_val):
            next_unit_ptr_address = queued_units_ptr + j * 4
            next_unit_ptr_data = read_process_memory(process_handle, next_unit_ptr_address, 4)
            if next_unit_ptr_data is None:
                queued_units_list.append(False)
                continue
            next_unit_ptr = ctypes.c_uint32.from_buffer_copy(next_unit_ptr_data).value
            # For queued units, assume the pointer is already a technoType pointer.
            next_unit_name = get_unit_name_from_techno_type(next_unit_ptr, process_handle, player_number)
            queued_units_list.append(next_unit_name)
        print(f"Player {player_number} ({factory_name}): Queued units: {queued_units_list}")

def read_techno_types():
    pid = find_pid_by_name("gamemd-spawn.exe")
    if pid is None:
        print("Could not find process")
        return

    process_handle = ctypes.windll.kernel32.OpenProcess(
        wintypes.DWORD(0x0010 | 0x0020 | 0x0008 | 0x0010), False, pid)

    # Fixed base pointers.
    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c

    fixedPointData = read_process_memory(process_handle, fixedPoint, 4)
    if fixedPointData is None:
        print("Failed to read fixedPoint")
        ctypes.windll.kernel32.CloseHandle(process_handle)
        return
    fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointData).value

    classBaseArrayData = read_process_memory(process_handle, classBaseArrayPtr, 4)
    if classBaseArrayData is None:
        print("Failed to read classBaseArrayPtr")
        ctypes.windll.kernel32.CloseHandle(process_handle)
        return
    classBaseArray = ctypes.c_uint32.from_buffer_copy(classBaseArrayData).value

    # Calculate the start of the player base pointer array.
    classbasearray = fixedPointValue + 1120 * 4

    for i in range(MAXPLAYERS):
        classBaseData = read_process_memory(process_handle, classbasearray, 4)
        classbasearray += 4
        if classBaseData is None:
            continue
        classBasePtr = ctypes.c_uint32.from_buffer_copy(classBaseData).value
        if classBasePtr == INVALIDCLASS:
            continue

        # Convert pointer index into an absolute address.
        realClassBasePtr = classBasePtr * 4 + classBaseArray
        realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)
        if realClassBaseData is None:
            continue
        realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBaseData).value

        # Process each factory type for this player.
        for factory_name, offset in FACTORIES:
            process_factory(realClassBase, process_handle, i, offset, factory_name)

    ctypes.windll.kernel32.CloseHandle(process_handle)

def main():
    while True:
        read_techno_types()
        time.sleep(0.5)

if __name__ == "__main__":
    main()
