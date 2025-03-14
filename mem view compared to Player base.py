import ctypes
from ctypes import wintypes
import psutil
import time

# Known offsets with their descriptions
KNOWN_OFFSETS = {
    # other
    0x2dc: "Credits spent",
    0x30c: "Balance",
    0x53a4: "Power output",
    0x53a8: "power drain",
    0x2f4: "Amount of infantry",
    0x5538: "infantry count",
    0x5588: "infantry count",
    0x53e4: "infantry lost",
    0x5434: "infantry lost",
    0x2e8: "number of vehicles",
    0x5574: "number of vehicles",
    0x78: "Number of structures placed",
    0x55b0: "total amount of structures placed",
    0x5560: "Number of structures placed",
    0x5510: "Number of structures (Even ones just in que and not ready. will go back down if cancelled)",
    0x2f0: "Number of structures (Even ones just in que and not ready. will go back down if cancelled)",
    0x270: "Infantry unit just made (1 = conscript, 2 = Tesla Trooper, 7 = Crazy Ivan, 8 = deso, 9 = soviet dog, "
           "25 = falk trooper,"
           "27 = soviet Engi, "
           "48 = Boris, "
           ")",
    0x26c: "Structure just placed (9 = tesla reactor, 10 = sov battle lab, 11 = soviet barracks, "
           "13 = soviet radar, 14 = sov WF, 15 = soviet Ore ref, 16 = sov wall, 20 = sentry gun, "
           "24 = iron certain"
           "26 = sov service depot, "
           "25 = soviet construction vehicle, 53 = tesla coil, "
           "54 = Nuke, "
           "65 = nuke power plant, 67 = flak track, "
           "310 = industrial plant, 359 = battle bunker)",
    0x274: "vehicle just made ("
           "1 = sov war miner, "
           "2 = apoc, "
           "3 = rhino tank, "
           "14 = v3 rocket launcher, "
           "15 = kirov, "
           "16 = Terror drone, "
           "17 = flak track, "
           "26 = Sov mcv"
           "67 = siege chopper, "
           ")",

    # infantry count

    # vehicle count
    0x158: "Soviet Miners",
    0x5524: "soviet MCV (Maybe)",

    # plane count
    0x2f8: "Sov spy plane",

    # building count
    0x60: "Soviet Construction Yard count",
    0x90: "Sov service depot",
    0x15c: "Soviet Ore refinerys",
    0x160: "Soviet War Factorys",
    0xf0: "Battle bunker count",
    0x537c: "Soviet Barracks count",

    0x5384: "Soviet Construction Yard count",

    # total amount of infantry made(includes clicking the icon and stopping)
    0x0b30: "Total amount of GI made",
    0x0b34: "Total amount of Conscript made",
    0x0b38: "Total amount of Tesla Trooper made",
    0x0b3c: "Total amount of Allied Engineer made",
    0x0b40: "Total amount of Rocketeer made",
    0x0b44: "Total amount of Navy SEAL made",
    0x0b48: "Total amount of Yuri Clone made",
    0x0b4c: "Total amount of Crazy Ivan made",
    0x0b50: "Total amount of Desolator made",
    0x0b54: "Total amount of Soviet Dog made",
    0x0b6c: "Total amount of Chrono Legionnaire made",
    0x0b70: "Total amount of Spy made",
    0x0b80: "Total amount of Yuri Prime made",
    0x0b84: "Total amount of Sniper made",
    0x0b90: "Total amount of Tanya made",
    0x0b94: "Total amount of Flak Trooper made",
    0x0b98: "Total amount of Terrorist made",
    0x0b9c: "Total amount of Soviet Engineer made",
    0x0ba0: "Total amount of Allied Dog made",
    0x0be4: "Total amount of Yuri Engineer made",
    0x0be8: "Total amount of Guardian GI (GGI) made",
    0x0bec: "Total amount of Initiate made",
    0x0bf0: "Total amount of Boris made",
    0x0bf4: "Total amount of Brute made",
    0x0bf8: "Total amount of Virus made",

    # total amount of vehicles made (includes clicking the icon and stopping)
    0x1338: "Total amount of Allied MCV made",
    0x133c: "Total amount of War Miners made",
    0x1340: "Total amount of Apocalypse Tanks made",
    0x1344: "Total amount of Rhino Tanks made",
    0x1348: "Total amount of Soviet Amphibious Transports made",
    0x135c: "Total amount of Grizzly Tanks made",
    0x136c: "Total amount of Aircraft Carriers made",
    0x1370: "Total amount of V3 Rocket Launchers made",
    0x1374: "Total amount of Kirov Airships made",
    0x1378: "Total amount of Terror Drones made",
    0x137c: "Total amount of Flak Tracks made",
    0x1380: "Total amount of Destroyers made",
    0x1384: "Total amount of Typhoon Attack Subs made",
    0x1388: "Total amount of Aegis Cruisers made",
    0x138c: "Total amount of Allied Amphibious Transports made",
    0x1390: "Total amount of Dreadnoughts made",
    0x1394: "Total amount of NightHawk Transports made",
    0x1398: "Total amount of Giant Squids made",
    0x139c: "Total amount of Dolphins made",
    0x13a0: "Total amount of Soviet MCVs made",
    0x13a4: "Total amount of Tank Destroyers made",
    0x13b4: "Total amount of Lasher Tanks made",
    0x13bc: "Total amount of Chrono Miners made",
    0x13c0: "Total amount of Prism Tanks made",
    0x13c8: "Total amount of Sea Scorpions made",
    0x13cc: "Total amount of Mirage Tanks made",
    0x13d0: "Total amount of IFVs made",
    0x13dc: "Total amount of Demolition Trucks made",
    0x1414: "Total amount of Yuri Amphibious Transports made",
    0x1418: "Total amount of Yuri MCVs made",
    0x141c: "Total amount of Slave Miners Undeployed made",
    0x1428: "Total amount of Gattling Tanks made",
    0x142c: "Total amount of Battle Fortresses made",
    0x1430: "Total amount of Chaos Drones made",
    0x1434: "Total amount of Magnetrons made",
    0x1440: "Total amount of Boomers made",
    0x1444: "Total amount of Siege Choppers made",
    0x144c: "Total amount of Masterminds made",
    0x1450: "Total amount of Flying Discs made",
    0x1458: "Total amount of Robot Tanks made",

    # total amount of planes made (includes clicking the icon and stopping)
    0x350: "amount of spy planes made",

    # total amount of buildings made (includes clicking the icon and stopping)
    0x1b40: "Total amount of Allied Power Plant ever built",
    0x1b44: "Total amount of Allied Ore Refinery ever built",
    0x1b48: "Total amount of Allied Con Yard ever built",
    0x1b4c: "Total amount of Allied Barracks ever built",
    0x1b54: "Total amount of Allied Service Depot ever built",
    0x1b58: "Total amount of Allied Battle Lab ever built",
    0x1b5c: "Total amount of Allied War Factory ever built",
    0x1b64: "Total amount of Tesla Reactor ever built",
    0x1b68: "Total amount of Soviet Battle Lab ever built",
    0x1b6c: "Total amount of Soviet Barracks ever built",
    0x1b74: "Total amount of Soviet Radar ever built",
    0x1b78: "Total amount of Soviet War Factory ever built",
    0x1b7c: "Total amount of Soviet Ore Refinery ever built",
    0x1b88: "Total amount of Yuri Radar ever built",
    0x1b90: "Total amount of Sentry Gun ever built",
    0x1b94: "Total amount of Patriot Missile ever built",
    0x1b9c: "Total amount of Allied Naval Yard ever built",
    0x1ba0: "Total amount of Iron Curtain ever built",
    0x1ba4: "Total amount of Soviet Con Yard ever built",
    0x1ba8: "Total amount of Soviet Service Depot ever built",
    0x1bac: "Total amount of Chrono Sphere ever built",
    0x1bb4: "Total amount of Weather Controller ever built",
    0x1c14: "Total amount of Tesla Coil ever built",
    0x1c18: "Total amount of Nuclear Missile Launcher ever built",
    0x1c34: "Total amount of Soviet Naval Yard ever built",
    0x1c38: "Total amount of SpySat Uplink ever built",
    0x1c3c: "Total amount of Gap Generator ever built",
    0x1c44: "Total amount of Nuclear Reactor ever built",
    0x1c48: "Total amount of PillBox ever built",
    0x1c4c: "Total amount of Flak Cannon ever built",
    0x1c5c: "Total amount of Oil Derrick ever built",
    0x1c60: "Total amount of Cloning Vats ever built",
    0x1c64: "Total amount of Ore Purifier ever built",
    0x1ce4: "Total amount of Allied AFC ever built",
    0x1d5c: "Total amount of American AFC ever built",
    0x1ff0: "Total amount of Yuri Con Yard ever built",
    0x1ff4: "Total amount of Bio Reactor ever built",
    0x1ff8: "Total amount of Yuri Barracks ever built",
    0x1ffc: "Total amount of Yuri War Factory ever built",
    0x2000: "Total amount of Yuri Naval Yard ever built",
    0x2008: "Total amount of Yuri Battle Lab ever built",
    0x2010: "Total amount of Gattling Cannon ever built",
    0x2014: "Total amount of Psychic Tower ever built",
    0x2018: "Total amount of Industrial Plant ever built",
    0x201c: "Total amount of Grinder ever built",
    0x2020: "Total amount of Genetic Mutator ever built",
    0x202c: "Total amount of Psychic Dominator ever built",
    0x2098: "Total amount of Tank Bunker ever built",
    0x20d0: "Total amount of Robot Control Center ever built",
    0x20d4: "Total amount of Slave Miner Deployed ever built",
    0x20dc: "Total amount of Battle Bunker ever built",

    # total amount of structures lost
    0x3b60: "Allied Power Plant lost",
    0x3b64: "Allied Ore Refinery lost",
    0x3b68: "Allied Con Yard lost",
    0x3b6c: "Allied Barracks lost",
    0x3b74: "Allied Service Depot lost",
    0x3b78: "Allied Battle Lab lost",
    0x3b7c: "Allied War Factory lost",
    0x3b84: "Tesla Reactor lost",
    0x3b88: "Soviet Battle Lab lost",
    0x3b8c: "Soviet Barracks lost",
    0x3b94: "Soviet Radar lost",
    0x3b98: "Soviet War Factory lost",
    0x3b9c: "Soviet Ore Refinery lost",
    0x3ba8: "Yuri Radar lost",
    0x3bb0: "Sentry Gun lost",
    0x3bb4: "Patriot Missile lost",
    0x3bbc: "Allied Naval Yard lost",
    0x3bc0: "Iron Curtain lost",
    0x3bc4: "Soviet Construction Yard lost",
    0x3bc8: "Soviet Service Depot lost",
    0x3bcc: "Chrono Sphere lost",
    0x3bd4: "Weather Controller lost",
    0x3c34: "Tesla Coil lost",
    0x3c38: "Nuclear Missile Launcher lost",
    0x3c4c: "Soviet Naval Yard lost",
    0x3c50: "SpySat Uplink lost",
    0x3c54: "Gap Generator lost",
    0x3c5c: "Nuclear Reactor lost",
    0x3c60: "PillBox lost",
    0x3c64: "Flak Cannon lost",
    0x3c74: "Oil Derrick lost",
    0x3c78: "Cloning Vats lost",
    0x3c7c: "Ore Purifier lost",
    0x3d04: "Allied AFC lost",
    0x3d7c: "American AFC lost",
    0x4010: "Yuri Construction Yard lost",
    0x4014: "Bio Reactor lost",
    0x4018: "Yuri Barracks lost",
    0x401c: "Yuri War Factory lost",
    0x4020: "Yuri Naval Yard lost",
    0x4028: "Yuri Battle Lab lost",
    0x4030: "Gattling Cannon lost",
    0x4034: "Psychic Tower lost",
    0x4038: "Industrial Plant lost",
    0x403c: "Grinder lost",
    0x4040: "Genetic Mutator lost",
    0x404c: "Psychic Dominator lost",
    0x40b8: "Tank Bunker lost",
    0x40f0: "Robot Control Center lost",
    0x40f4: "Slave Miner Deployed lost",
    0x40fc: "Battle Bunker lost",

    # total amount lost infantry lost
    0x2b50: "GI lost",
    0x2b54: "Conscripts lost",
    0x2b58: "Tesla Troopers lost",
    0x2b5c: "Allied Engineer lost",
    0x2b60: "Rocketeer lost",
    0x2b64: "Navy SEAL lost",
    0x2b68: "Yuri Clone lost",
    0x2b6c: "Crazy Ivan lost",
    0x2b70: "Desolator lost",
    0x2b74: "Soviet Dog lost",
    0x2b8c: "Chrono Legionnaire lost",
    0x2b90: "Spy lost",
    0x2ba0: "Yuri Prime lost",
    0x2ba4: "Sniper lost",
    0x2bb0: "Tanya lost",
    0x2bb4: "Flak Trooper lost",
    0x2bb8: "Terrorist lost",
    0x2bbc: "Soviet Engineer lost",
    0x2bc0: "Allied Dog lost",
    0x2c04: "Yuri Engineer lost",
    0x2c08: "Guardian GI (GGI) lost",
    0x2c0c: "Initiate lost",
    0x2c10: "Boris lost",
    0x2c14: "Brute lost",
    0x2c18: "Virus lost",

    # total amount of vehicles lost
    0x3358: "Allied MCV lost",
    0x335c: "War Miner lost",
    0x3360: "Apocalypse Tank lost",
    0x3364: "Rhino Tank lost",
    0x3368: "Soviet Amphibious Transport lost",
    0x337c: "Grizzly Tank lost",
    0x338c: "Aircraft Carrier lost",
    0x3390: "V3 Rocket Launcher lost",
    0x3394: "Kirov Airship lost",
    0x3398: "Terror Drone lost",
    0x339c: "Flak Track lost",
    0x33a0: "Destroyer lost",
    0x33a4: "Typhoon Attack Sub lost",
    0x33a8: "Aegis Cruiser lost",
    0x33ac: "Allied Amphibious Transport lost",
    0x33b0: "Dreadnought lost",
    0x33b4: "NightHawk Transport lost",
    0x33b8: "Giant Squid lost",
    0x33bc: "Dolphin lost",
    0x33c0: "Soviet MCV lost",
    0x33c4: "Tank Destroyer lost",
    0x33d4: "Lasher Tank lost",
    0x33dc: "Chrono Miner lost",
    0x33e0: "Prism Tank lost",
    0x33e8: "Sea Scorpion lost",
    0x33ec: "Mirage Tank lost",
    0x33f0: "IFV lost",
    0x33fc: "Demolition Truck lost",
    0x3434: "Yuri Amphibious Transport lost",
    0x3438: "Yuri MCV lost",
    0x343c: "Slave Miner Undeployed lost",
    0x3448: "Gattling Tank lost",
    0x344c: "Battle Fortress lost",
    0x3450: "Chaos Drone lost",
    0x3454: "Magnetron lost",
    0x3460: "Boomer lost",
    0x3464: "Siege Chopper lost",
    0x346c: "Mastermind lost",
    0x3470: "Flying Disc lost",
    0x3478: "Robot Tank lost",

    # useless wierd

    # puzzling
    0x310: "(has a sov ref?? amount of sov refs??) (starts at 0. + 200 for every extra ore ref. decrements by 200 when sold or destroyed)",
    0x88: "(something to do with service depot",
    0x8c: "(something to do with service depot",

    0x144: "somthing to do with industrial plant",
    0x148: "somthing to do with industrial plant",
    0x14c: "somthing to do with industrial plant",
    0x150: "somthing to do with industrial plant (activates the bonus? 1 = active, 0 = not active)",

    0x2a4: "something to do with force shield",
    0x2a8: "something to do with force shield",
    0x2ac: "something to do with force shield",

    0xe4: "something to do with battle bunker (only first time made)",
    0xe8: "something to do with battle bunker (only first time made)",
    0xec: "something to do with battle bunker (only first time made)",

    0x57a4: "Adds around 360 every second (Game time?)",

    0x57a8: "scrolling around the map???",

    0x5490: "(changes to huge number when undeployed and 0 when deployed) (Also changes to a huge number when placing tesla reactor and selling reactor as well). (then i blocked it)",
    0x5730: "deploying soviet mcv makes this 20, undeploying makes this 0. then i placed a tesla reactor and it turned 30 selling made it 20 again (then i blocked it)",

    0x53bc: "when i click a structure this goes super high and back to 0 when i cancel or place (what is being built??) (BLOCKED)",

    0x55a4: "went from 0 to super high when i placed tesla reactor (283261376) (BLOCKED)",
    0x55a8: "went from 0 to 19 when i placed tesla reactor",
    0x55ac: "went from 1 to 257 when i placed tesla reactor",
    0x5724: "went 49918736 -> 259478592 when i placed tesla reactor (BLOCKED)",
    0x575c: "went 9 -> 11 when i placed tesla reactor. 6 -> 9 when i placed second tesla reactor (BLOCKED)",
    0x5728: "went 20 -> 30 when i placed tesla reactor. 30 -> 50 when i placed second tesla reactor (BLOCKED)",
    0x5760: "went 6 -> 10 when i placed tesla reactor. 10 -> 14 when i placed second tesla reactor (BLOCKED)",
    0x5758: "went 25 -> 21 when i placed second tesla reactor (BLOCKED)",

    0x552c: "went 0 -> 285645296 when i sold tesla reactor (Blocked)",
    0x5530: "went 0 -> 11 when i sold tesla reactor",
    0x5534: "went 1 -> 257 when i sold tesla reactor",

    0x557c: "went 0 -> 285644624 when i sold tesla reactor (BLOCKED)",

    0x32f4c: "Timer?? game time??",
    0x1b86c: "Timer?? game time?? (Best one yet)",
    0x510dc: "Game Timer??",
    0x1ce54: "Game Timer??"
}

# 0x5c378 (66 = something is ready to be placed, 0 = something is being made, 4266851961 =
# 0x5c5d4
# 0x5c598
# 0x5c614


IGNORED_OFFSETS = []  # This list is optional now

MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff
SCAN_SIZE = 0x100
START_OFFSET = 0x0  # Variable to control how far ahead the scan starts
INT_SIZE = 4  # Size of an integer in bytes


class GameData:
    def __init__(self):
        self.validPlayer = [False] * MAXPLAYERS


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


def print_memory_range(process_handle, realClassBase):
    # Iterate over the range starting from realClassBase + START_OFFSET
    for offset in range(START_OFFSET, START_OFFSET + SCAN_SIZE, INT_SIZE):
        address = realClassBase + offset
        try:
            # Read the current integer value from memory
            current_value = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, address, INT_SIZE)).value

            # Check if the offset is in the KNOWN_OFFSETS dictionary
            if offset in KNOWN_OFFSETS:
                description = KNOWN_OFFSETS[offset]
                print(f"Offset {hex(offset)}: {current_value} ({description})")
            else:
                # If not in KNOWN_OFFSETS, just print the value
                print(f"Offset {hex(offset)}: {current_value}")

        except Exception as e:
            # Handle cases where memory could not be read
            print(f"Failed to read memory at address {hex(address)}: {e}")


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

    for i in range(MAXPLAYERS):
        classBasePtr = ctypes.c_uint32.from_buffer_copy(read_process_memory(process_handle, classbasearray, 4)).value
        classbasearray += 4
        if classBasePtr != INVALIDCLASS:
            game_data.validPlayer[i] = True
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBase = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, realClassBasePtr, 4)).value

            # Print the memory values in the defined range
            print(f"Player {i}:")
            print_memory_range(process_handle, realClassBase)
            print("-" * 40)

    ctypes.windll.kernel32.CloseHandle(process_handle)


def ra2_main():
    game_data = GameData()

    while True:
        if not find_pid_by_name("gamemd-spawn.exe"):
            print("Game is not running, waiting...")
            time.sleep(1)
            continue

        read_class_base_mem(game_data)

        # Wait for the user to press Enter before continuing
        input("Press Enter to print the next set of memory values...")


if __name__ == "__main__":
    ra2_main()
