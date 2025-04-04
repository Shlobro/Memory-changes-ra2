import ctypes
import psutil
import time
from ctypes import wintypes

MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff
INFOFFSET = 0x557c

ALLIDOGOFFSET = 0x1c
SOVDOGOFFSET = 0x9

TANKOFFSET = 0x5568
ALLITANKOFFSET = 0x9
SOVTANKOFFSET = 0x3
ALLIMINEROFFSET = 0x84 // 4
SOVMINEROFFSET = 0x4 // 4

BUILDINGOFFSET = 0x5554
ALLIWARFACTORYOFFSET = 0x1c // 4
SOVWARFACTORYOFFSET = 0x38 // 4

CREDITSPENT_OFFSET = 0x2dc
BALANCEOFFSET = 0x30c
USERNAMEOFFSET = 0x1602a
ISWINNEROFFSET = 0x1f7
ISLOSEROFFSET = 0x1f8

POWEROUTPUTOFFSET = 0x53a4
POWERDRAINOFFSET = 0x53a8

PRODUCINGBUILDINGINDEXOFFSET = 0x564c
PRODUCINGUNITINDEXOFFSET = 0x5650

HOUSETYPECLASSBASEOFFSET = 0x34
COUNTRYSTRINGOFFSET = 0x24

COLOROFFSET = 0x56fC
COLORSCHEMEOFFSET = 0x16054

ROCKETEEROFFSET = 0x04
SPIDEROFFSET = 0x10

IFVOFFSET = 0x26
FLAKTRACKOFFSET = 0x11

CONSCRIPTOFFSET = 0x01
GIOFFSET = 0x0

SUBMARINEOFFSET = 0x13
DESTROYEROFFSET = 0x12

DOPHINOFFSET = 0x19
SQUIDOFFSET = 0x18

CVOFFSET = 0x0d  # aircraft carrier
DREADNOUGHTOFFSET = 0x16  # SOV


class Player:
    def __init__(self, index, process_handle, real_class_base):
        self.index = index
        self.process_handle = process_handle
        self.real_class_base = real_class_base

        self.username = ctypes.create_unicode_buffer(0x20)
        self.color = ""
        self.country_name = ctypes.create_string_buffer(0x40)

        self.is_winner = False
        self.is_loser = False

        self.balance = 0
        self.spent_credit = 0
        self.power_output = 0
        self.power_drain = 0

        self.allied_war_factory_count = 0  # Attribute for storing Allied War Factory count

        # Pointers to arrays
        self.unit_array_ptr = None  # Pointer to the units array
        self.building_array_ptr = None  # Pointer to the buildings array
        self.infantry_array_ptr = None  # Pointer to the infantry array

        # Initialize the pointers by reading memory
        self.initialize_pointers()

    def initialize_pointers(self):
        """ Initialize the pointers for the arrays of units, buildings, and infantry. """

        # Step 1: Read the pointer to the units array (use the TANKOFFSET)
        tank_offset = 0x5568  # Replace with the actual offset for tanks/units
        tank_ptr_address = self.real_class_base + tank_offset
        tank_ptr_data = read_process_memory(self.process_handle, tank_ptr_address, 4)
        if tank_ptr_data:
            self.unit_array_ptr = int.from_bytes(tank_ptr_data, byteorder='little')

        # Step 2: Read the pointer to the buildings array (use the BUILDINGOFFSET)
        building_offset = 0x5554  # Replace with the actual offset for buildings
        building_ptr_address = self.real_class_base + building_offset
        building_ptr_data = read_process_memory(self.process_handle, building_ptr_address, 4)
        if building_ptr_data:
            self.building_array_ptr = int.from_bytes(building_ptr_data, byteorder='little')

        # Step 3: Read the pointer to the infantry array (use the INFOFFSET)
        infantry_offset = 0x557c  # Replace with the actual offset for infantry
        infantry_ptr_address = self.real_class_base + infantry_offset
        infantry_ptr_data = read_process_memory(self.process_handle, infantry_ptr_address, 4)
        if infantry_ptr_data:
            self.infantry_array_ptr = int.from_bytes(infantry_ptr_data, byteorder='little')

    def get_building_count(self, building_offset):
        """ Read a specific building count using the offset from the building array. """
        if self.building_array_ptr is None:
            return 0  # Return 0 if the building array pointer is not initialized

        specific_building_address = self.building_array_ptr + building_offset
        building_data = read_process_memory(self.process_handle, specific_building_address, 4)
        if building_data:
            return int.from_bytes(building_data, byteorder='little')
        return 0

    def get_unit_count(self, unit_offset):
        """ Read a specific unit count using the offset from the unit array. """
        if self.unit_array_ptr is None:
            return 0  # Return 0 if the unit array pointer is not initialized

        specific_unit_address = self.unit_array_ptr + unit_offset
        unit_data = read_process_memory(self.process_handle, specific_unit_address, 4)
        if unit_data:
            return int.from_bytes(unit_data, byteorder='little')
        return 0

    def get_infantry_count(self, infantry_offset):
        """ Read a specific infantry count using the offset from the infantry array. """
        if self.infantry_array_ptr is None:
            return 0  # Return 0 if the infantry array pointer is not initialized

        specific_infantry_address = self.infantry_array_ptr + infantry_offset
        infantry_data = read_process_memory(self.process_handle, specific_infantry_address, 4)
        if infantry_data:
            return int.from_bytes(infantry_data, byteorder='little')
        return 0

    def update_dynamic_data(self):
        # Balance
        balance_ptr = self.real_class_base + BALANCEOFFSET
        balance_data = read_process_memory(self.process_handle, balance_ptr, 4)
        if balance_data is None:
            print(f"Player {self.index}: Unable to read balance, game might be closed.")
            return

        self.balance = ctypes.c_uint32.from_buffer_copy(balance_data).value
        print(f"Player {self.index} balance {self.balance}")

        # Spent credit
        spent_credit_ptr = self.real_class_base + CREDITSPENT_OFFSET
        spent_credit_data = read_process_memory(self.process_handle, spent_credit_ptr, 4)
        if spent_credit_data is None:
            print(f"Player {self.index}: Unable to read spent credit, game might be closed.")
            return

        self.spent_credit = ctypes.c_uint32.from_buffer_copy(spent_credit_data).value
        print(f"Player {self.index} spent credit {self.spent_credit}")

        # IsWinner
        is_winner_ptr = self.real_class_base + ISWINNEROFFSET
        is_winner_data = read_process_memory(self.process_handle, is_winner_ptr, 1)
        if is_winner_data is None:
            print(f"Player {self.index}: Unable to read winner status, game might be closed.")
            return

        self.is_winner = bool(ctypes.c_uint8.from_buffer_copy(is_winner_data).value)
        print(f"Player {self.index} is winner {self.is_winner}")

        # IsLoser
        is_loser_ptr = self.real_class_base + ISLOSEROFFSET
        is_loser_data = read_process_memory(self.process_handle, is_loser_ptr, 1)
        if is_loser_data is None:
            print(f"Player {self.index}: Unable to read loser status, game might be closed.")
            return

        self.is_loser = bool(ctypes.c_uint8.from_buffer_copy(is_loser_data).value)
        print(f"Player {self.index} is loser {self.is_loser}")

        # Power output
        power_output_ptr = self.real_class_base + POWEROUTPUTOFFSET
        power_output_data = read_process_memory(self.process_handle, power_output_ptr, 4)
        if power_output_data is None:
            print(f"Player {self.index}: Unable to read power output, game might be closed.")
            return

        self.power_output = ctypes.c_uint32.from_buffer_copy(power_output_data).value
        print(f"Player {self.index} power output {self.power_output}")

        # Power drain
        power_drain_ptr = self.real_class_base + POWERDRAINOFFSET
        power_drain_data = read_process_memory(self.process_handle, power_drain_ptr, 4)
        if power_drain_data is None:
            print(f"Player {self.index}: Unable to read power drain, game might be closed.")
            return

        self.power_drain = ctypes.c_uint32.from_buffer_copy(power_drain_data).value
        print(f"Player {self.index} power drain {self.power_drain}")


class GameData:
    def __init__(self):
        self.players = []
        self.currentGameRunning = False

    def add_player(self, player):
        self.players.append(player)

    def update_all_players(self):
        for player in self.players:
            player.update_dynamic_data()


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
        if e.winerror == 299:  # Only part of a ReadProcessMemory request was completed
            print("Memory read incomplete. Game might still be loading. Retrying...")
            time.sleep(1)
            return None
        else:
            raise


# Define the mapping of color scheme values to actual color names
COLOR_SCHEME_MAPPING = {
    3: "Yellow",
    5: "White",
    7: "Grey",
    11: "Red",
    13: "Orange",
    15: "Pink",
    17: "Purple",
    21: "Blue",
    25: "Cyan",
    29: "Green"
}


# Function to convert color scheme number to color name
def get_color_name(color_scheme):
    return COLOR_SCHEME_MAPPING.get(color_scheme, "Unknown")


# Modify the initialize_game_data function to convert and store the color names
def initialize_players(game_data, process_handle):
    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c

    fixedPointValue = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, fixedPoint, 4)).value
    classBaseArray = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, classBaseArrayPtr, 4)).value

    classbasearray = fixedPointValue + 1120 * 4
    valid_player_count = 0

    for i in range(MAXPLAYERS):
        memory_data = read_process_memory(process_handle, classbasearray, 4)
        if memory_data is None:
            print(f"Skipping player {i} due to incomplete memory read.")
            continue

        classBasePtr = ctypes.c_uint32.from_buffer_copy(memory_data).value
        classbasearray += 4
        if classBasePtr != INVALIDCLASS:
            valid_player_count += 1
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)

            if realClassBaseData is None:
                print(f"Skipping player {i} due to incomplete real class base read.")
                continue

            realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBaseData).value

            player = Player(i, process_handle, realClassBase)

            # Set the color
            colorPtr = realClassBase + COLORSCHEMEOFFSET
            color_data = read_process_memory(process_handle, colorPtr, 4)
            if color_data is None:
                print(f"Skipping color assignment for player {i} due to incomplete memory read.")
                continue
            color_scheme_value = ctypes.c_uint32.from_buffer_copy(color_data).value
            player.color = get_color_name(color_scheme_value)
            print(f"Player {i} colorScheme {player.color}")

            # Set the country name
            houseTypeClassBasePtr = realClassBase + HOUSETYPECLASSBASEOFFSET
            houseTypeClassBaseData = read_process_memory(process_handle, houseTypeClassBasePtr, 4)
            if houseTypeClassBaseData is None:
                print(f"Skipping country name assignment for player {i} due to incomplete memory read.")
                continue
            houseTypeClassBase = ctypes.c_uint32.from_buffer_copy(houseTypeClassBaseData).value
            countryNamePtr = houseTypeClassBase + COUNTRYSTRINGOFFSET
            country_data = read_process_memory(process_handle, countryNamePtr, 25)
            if country_data is None:
                print(f"Skipping country name assignment for player {i} due to incomplete memory read.")
                continue
            ctypes.memmove(player.country_name, country_data, 25)
            print(f"Player {i} country name {player.country_name.value.decode('utf-8')}")

            # Set the username

            userNamePtr = realClassBase + USERNAMEOFFSET
            print("!!!!!!!!!!!!!!", hex(userNamePtr))
            username_data = read_process_memory(process_handle, userNamePtr, 0x20)
            if username_data is None:
                print(f"Skipping username assignment for player {i} due to incomplete memory read.")
                continue
            ctypes.memmove(player.username, username_data, 0x20)
            print(f"Player {i} name {player.username.value}")

            game_data.add_player(player)

    print(f"Number of valid players: {valid_player_count}")
    return valid_player_count


def ra2_main():
    game_data = GameData()

    while True:
        # Loop until the game process is detected
        while True:
            pid = find_pid_by_name("gamemd-spawn.exe")
            if pid is not None:
                break
            print("Waiting for the game to start...")
            time.sleep(1)

        # Obtain the process handle
        process_handle = ctypes.windll.kernel32.OpenProcess(
            wintypes.DWORD(0x0010 | 0x0020 | 0x0008 | 0x0010), False, pid)

        # Loop until at least one valid player is detected
        while True:
            valid_player_count = initialize_players(game_data, process_handle)
            if valid_player_count > 0:
                break
            print("Waiting for at least one valid player...")
            time.sleep(1)

        # Read dynamic data continuously
        while True:
            if find_pid_by_name("gamemd-spawn.exe") is None:
                print("Game process ended.")
                break

            game_data.update_all_players()
            time.sleep(1)

        ctypes.windll.kernel32.CloseHandle(process_handle)
        print("Waiting for the game to start again...")


if __name__ == "__main__":
    ra2_main()
