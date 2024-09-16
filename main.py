import psutil
import ctypes
from ctypes import wintypes
import time

# Define constants and structures
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

#CONSCRIPTOFFSET = 0x01
GIOFFSET = 0x0

SUBMARINEOFFSET = 0x13
DESTROYEROFFSET = 0x12

DOPHINOFFSET = 0x19
SQUIDOFFSET = 0x18

CVOFFSET = 0x0d  # aircraft carrier
DREADNOUGHTOFFSET = 0x16  # SOV


##Experiments
AMOUNTOFINFANTRYOFFSET = 0x2f4

CONSCRIPTOFFSET = 0xb34

SOVIETMCVOFFSET = 0x2e8 # does this start with 1 more? (meaning if you have 1 mcv it shows 2)

SOVIETCONSTRUCTIONYARDOFFSET = 0x60

#REALLY MAYBE
NUMBEROFSTRUCTURES = 0x78 # not ready
NUMBEROFSTRUCTURES2 = 0x2f0 # ready? placed?
TECHLEVEL = 0x26c # what can be built for this player???? what he can make? weird
INFANTRYUNITBEINGMADE = 0x270 # 1 = conscript. 9 = sov dog

class ColorStruct(ctypes.Structure):
    _fields_ = [("rgb", ctypes.c_uint8 * 3)]

# Placeholder for game data
allieCountries = ["Americans", "Alliance", "French", "Germans", "British"]
sovietCountries = ["Africans", "Arabs", "Confederation", "Russians"]

class GameData:
    def __init__(self):
        self.balance = [0] * MAXPLAYERS
        self.spentCredit = [0] * MAXPLAYERS
        self.UserName = [ctypes.create_unicode_buffer(0x20) for _ in range(MAXPLAYERS)]
        self.isWinner = [False] * MAXPLAYERS
        self.isLoser = [False] * MAXPLAYERS
        self.powerOutput = [0] * MAXPLAYERS
        self.powerDrain = [0] * MAXPLAYERS
        self.color = [0] * MAXPLAYERS
        self.countryName = [ctypes.create_string_buffer(0x40) for _ in range(MAXPLAYERS)]
        self.GIcount = [0] * MAXPLAYERS
        self.ALLIDOGcount = [0] * MAXPLAYERS
        self.SOVDOGcount = [0] * MAXPLAYERS
        self.ALLITANKcount = [0] * MAXPLAYERS
        self.SOVTANKcount = [0] * MAXPLAYERS
        self.ALLIMinerCount = [0] * MAXPLAYERS
        self.SOVMinerCount = [0] * MAXPLAYERS
        self.ALLIWarFactoryCount = [0] * MAXPLAYERS
        self.SOVWarFactoryCount = [0] * MAXPLAYERS
        self.playerColor = [ColorStruct() for _ in range(MAXPLAYERS)]
        self.validPlayer = [False] * MAXPLAYERS
        self.currentGameRunning = False

# Function to find the process ID by name
def find_pid_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None

# Function to read memory from another process
def read_process_memory(process_handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t()
    if ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytesRead)):
        return buffer.raw
    else:
        raise ctypes.WinError()

# Function to read class base and player data
def read_class_base(game_data):
    pid = find_pid_by_name("gamemd-spawn.exe")
    if pid is None:
        print("Could not find process")
        return

    process_handle = ctypes.windll.kernel32.OpenProcess(
        wintypes.DWORD(0x0010 | 0x0020 | 0x0008 | 0x0010), False, pid)

    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c

    fixedPointValue = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, fixedPoint, 4)).value
    classBaseArray = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, classBaseArrayPtr, 4)).value

    classbasearray = fixedPointValue + 1120 * 4
    for i in range(MAXPLAYERS):
        classBasePtr = ctypes.c_uint32.from_buffer_copy(
            read_process_memory(process_handle, classbasearray, 4)).value
        classbasearray += 4
        if classBasePtr != INVALIDCLASS:
            game_data.validPlayer[i] = True
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBase = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, realClassBasePtr, 4)).value

            # Balance
            balancePtr = realClassBase + BALANCEOFFSET
            game_data.balance[i] = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, balancePtr, 4)).value
            print(f"Player {i} balance {game_data.balance[i]}")

            # Spent money
            spentCreditPtr = realClassBase + CREDITSPENT_OFFSET
            game_data.spentCredit[i] = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, spentCreditPtr, 4)).value
            print(f"Player {i} spent {game_data.spentCredit[i]}")

            # User name
            userNamePtr = realClassBase + USERNAMEOFFSET
            ctypes.memmove(game_data.UserName[i],
                           read_process_memory(process_handle, userNamePtr, 0x20), 0x20)
            print(f"Player {i} name {game_data.UserName[i].value}")

            # IsWinner
            isWinnerPtr = realClassBase + ISWINNEROFFSET
            game_data.isWinner[i] = bool(ctypes.c_uint8.from_buffer_copy(
                read_process_memory(process_handle, isWinnerPtr, 1)).value)
            print(f"Player {i} isWinner {game_data.isWinner[i]}")

            # IsLoser
            isLoserPtr = realClassBase + ISLOSEROFFSET
            game_data.isLoser[i] = bool(ctypes.c_uint8.from_buffer_copy(
                read_process_memory(process_handle, isLoserPtr, 1)).value)
            print(f"Player {i} isLoser {game_data.isLoser[i]}")

            # Power output
            powerOutputPtr = realClassBase + POWEROUTPUTOFFSET
            game_data.powerOutput[i] = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, powerOutputPtr, 4)).value
            print(f"Player {i} powerOutput {game_data.powerOutput[i]}")

            # Power drain
            powerDrainPtr = realClassBase + POWERDRAINOFFSET
            game_data.powerDrain[i] = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, powerDrainPtr, 4)).value
            print(f"Player {i} powerDrain {game_data.powerDrain[i]}")

            # Player color scheme
            colorPtr = realClassBase + COLORSCHEMEOFFSET
            game_data.color[i] = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, colorPtr, 4)).value
            print(f"Player {i} colorScheme {game_data.color[i]}")

            # HouseTypeClassBase
            houseTypeClassBasePtr = realClassBase + HOUSETYPECLASSBASEOFFSET
            houseTypeClassBase = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, houseTypeClassBasePtr, 4)).value
            print(f"Player {i} houseTypeClassBase {houseTypeClassBase}")

            # Country name
            countryNamePtr = houseTypeClassBase + COUNTRYSTRINGOFFSET
            ctypes.memmove(game_data.countryName[i],
                           read_process_memory(process_handle, countryNamePtr, 25), 25)
            print(f"Player {i} countryName {game_data.countryName[i].value.decode('utf-8')}")

            # Read and process other fields similarly...
        else:
            game_data.validPlayer[i] = False

    ctypes.windll.kernel32.CloseHandle(process_handle)




def read_class_base_mem(game_data):
    pid = find_pid_by_name("gamemd-spawn.exe")
    if pid is None:
        print("Could not find process")
        return

    process_handle = ctypes.windll.kernel32.OpenProcess(
        wintypes.DWORD(0x0010 | 0x0020 | 0x0008 | 0x0010), False, pid)

    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c
    base_address = 0xe91f000  # Base address for comparison

    fixedPointValue = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, fixedPoint, 4)).value
    classBaseArray = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, classBaseArrayPtr, 4)).value

    classbasearray = fixedPointValue + 1120 * 4
    for i in range(MAXPLAYERS):
        classBasePtr = ctypes.c_uint32.from_buffer_copy(
            read_process_memory(process_handle, classbasearray, 4)).value
        classbasearray += 4
        if classBasePtr != INVALIDCLASS:
            game_data.validPlayer[i] = True
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBase = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, realClassBasePtr, 4)).value



            # Balance
            balancePtr = realClassBase + BALANCEOFFSET
            print(f"Player {i} balance absolute address: {hex(balancePtr)}, relative offset: {hex(balancePtr - base_address)}")

            # Spent money
            spentCreditPtr = realClassBase + CREDITSPENT_OFFSET
            print(f"Player {i} spentCredit absolute address: {hex(spentCreditPtr)}, relative offset: {hex(spentCreditPtr - base_address)}")

            # User name
            userNamePtr = realClassBase + USERNAMEOFFSET
            print(f"Player {i} userName absolute address: {hex(userNamePtr)}, relative offset: {hex(userNamePtr - base_address)}")

            # IsWinner
            isWinnerPtr = realClassBase + ISWINNEROFFSET
            print(f"Player {i} isWinner absolute address: {hex(isWinnerPtr)}, relative offset: {hex(isWinnerPtr - base_address)}")

            # IsLoser
            isLoserPtr = realClassBase + ISLOSEROFFSET
            print(f"Player {i} isLoser absolute address: {hex(isLoserPtr)}, relative offset: {hex(isLoserPtr - base_address)}")

            # Power output
            powerOutputPtr = realClassBase + POWEROUTPUTOFFSET
            print(f"Player {i} powerOutput absolute address: {hex(powerOutputPtr)}, relative offset: {hex(powerOutputPtr - base_address)}")

            # Power drain
            powerDrainPtr = realClassBase + POWERDRAINOFFSET
            print(f"Player {i} powerDrain absolute address: {hex(powerDrainPtr)}, relative offset: {hex(powerDrainPtr - base_address)}")

            # Player color scheme
            colorPtr = realClassBase + COLORSCHEMEOFFSET
            print(f"Player {i} colorScheme absolute address: {hex(colorPtr)}, relative offset: {hex(colorPtr - base_address)}")

            # HouseTypeClassBase
            houseTypeClassBasePtr = realClassBase + HOUSETYPECLASSBASEOFFSET
            houseTypeClassBase = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, houseTypeClassBasePtr, 4)).value
            print(f"Player {i} houseTypeClassBase absolute address: {hex(houseTypeClassBasePtr)}, relative offset: {hex(houseTypeClassBasePtr - base_address)}")

            # Country name
            countryNamePtr = houseTypeClassBase + COUNTRYSTRINGOFFSET
            print(f"Player {i} countryName absolute address: {hex(countryNamePtr)}, relative offset: {hex(countryNamePtr - base_address)}")

            # Add similar print statements for other fields if needed...

        else:
            game_data.validPlayer[i] = False

    ctypes.windll.kernel32.CloseHandle(process_handle)




def ra2_main():
    game_data = GameData()
    while True:
        if not find_pid_by_name("gamemd-spawn.exe"):
            game_data.currentGameRunning = False
            time.sleep(1)
            continue

        game_data.currentGameRunning = True
        read_class_base(game_data)
        read_class_base_mem(game_data)
        time.sleep(1)

if __name__ == "__main__":
    ra2_main()
