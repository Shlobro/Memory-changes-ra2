import ctypes
import psutil
from ctypes import wintypes

INVALIDCLASS = 0xffffffff

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
        return None

def main():
    # Locate the target process
    pid = find_pid_by_name("gamemd-spawn.exe")
    if pid is None:
        print("Process 'gamemd-spawn.exe' not found.")
        return

    # Open process with required access
    process_handle = ctypes.windll.kernel32.OpenProcess(
        wintypes.DWORD(0x0010 | 0x0020 | 0x0008 | 0x0010), False, pid)
    if not process_handle:
        print("Failed to open process.")
        return

    # Fixed addresses as per your original code
    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c

    # Read fixed point value
    fixedPointValue_raw = read_process_memory(process_handle, fixedPoint, 4)
    if fixedPointValue_raw is None:
        print("Failed to read fixedPoint.")
        return
    fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointValue_raw).value

    # Read class base array pointer
    classBaseArray_raw = read_process_memory(process_handle, classBaseArrayPtr, 4)
    if classBaseArray_raw is None:
        print("Failed to read classBaseArray.")
        return
    classBaseArray = ctypes.c_uint32.from_buffer_copy(classBaseArray_raw).value

    # Compute the base pointer for the class base array for player 0
    classbasearray = fixedPointValue + 4480

    # Read the class pointer for player 0
    player_pointer_address = classbasearray
    classBasePtr_raw = read_process_memory(process_handle, player_pointer_address, 4)
    if classBasePtr_raw is None:
        print("Failed to read player pointer at address:", hex(player_pointer_address))
        return
    classBasePtr = ctypes.c_uint32.from_buffer_copy(classBasePtr_raw).value

    if classBasePtr == INVALIDCLASS:
        print("Invalid class pointer for player 0.")
        return

    # Calculate the real class base pointer address
    realClassBasePtr = classBasePtr * 4 + classBaseArray
    realClassBase_raw = read_process_memory(process_handle, realClassBasePtr, 4)
    if realClassBase_raw is None:
        print("Failed to read real class base pointer at address:", hex(realClassBasePtr))
        return
    realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBase_raw).value

    # The player base address is now determined.
    player_base = realClassBase

    print(f"Player base address: {hex(player_base)}")
    print("Enter hexadecimal offsets (e.g., 0x557c) to see the pointer at that location.")
    print("Enter 'q' to exit.\n")

    # Loop to allow user to enter offsets continuously
    while True:
        offset_input = input("Enter offset (hex): ").strip()
        if offset_input.lower() == 'q':
            break

        try:
            user_offset = int(offset_input, 16)
        except ValueError:
            print("Invalid input. Please enter a valid hexadecimal number or 'q' to quit.")
            continue

        # Calculate the pointer address using the user-supplied offset
        pointer_address = player_base + user_offset
        print(f"Computed address: {hex(pointer_address)}")

        # Read the value at the computed pointer address (assuming it's a pointer)
        pointer_value_raw = read_process_memory(process_handle, pointer_address, 4)
        if pointer_value_raw is None:
            print(f"Failed to read pointer value at address {hex(pointer_address)}.")
        else:
            pointer_value = ctypes.c_uint32.from_buffer_copy(pointer_value_raw).value
            print(f"Value at {hex(pointer_address)}: {hex(pointer_value)}")

    ctypes.windll.kernel32.CloseHandle(process_handle)

if __name__ == "__main__":
    main()
