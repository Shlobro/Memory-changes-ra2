import ctypes
import time
from ctypes import wintypes

import psutil

# Known offsets with their descriptions
KNOWN_OFFSETS = {
    0x24: "COUNTRYSTRINGOFFSET",
    0x34: "HOUSETYPECLASSBASEOFFSET",
    0x60: "Construction Yard count",
    0x70: "when i made second tank bunker 10 -> 20",
    0x78: "no clue goes up slowly when i make structure. like +4 for afc. +1 for allied service depot etc and goes down when you lose stuff",
    0x84: "something to do with service depot?",
    0x88: "(something to do with service depot",
    0x8c: "(something to do with service depot",
    0x90: "amount of service depot (allied and soviet and civ captured)",
    0x9c: "when i made a grinder 0 -> 259953408",
    0xa0: "when i made a grinder 0 -> 10 ",
    0xa4: "when i made a grinder 1734934529 -> 1734934785",
    0xa8: "number of grinders",
    0xc0: "number of bio reactors?",
    0xcc: "when i made tank bunker 0 -> 279128848",
    0xd0: "when i made tank bunker 0 -> 10",
    0xd4: "when i made tank bunker 1702035457 -> 1702035713",
    0xd8: "number of tank bunkers",
    0xe4: "something to do with battle bunker (only first time made)",
    0xe8: "something to do with battle bunker (only first time made)",
    0xec: "something to do with battle bunker (only first time made)",
    0xf0: "Battle bunker count",
    0xfc: "when I made bio reactor 0 -> 279125536",
    0x100: "when I made bio reactor 0 -> 10",
    0x104: "when I made bio reactor 774766593 -> 774766849",
    0x108: "when I made bio reactor 0 -> 1",
    0x12c: "went up as soon as i put yuri radar 0 -> 260024688",
    0x130: "went up as soon as i put yuri radar 0 -> 10",
    0x134: "went up as soon as i put yuri radar 1851850753 -> 1851851009",
    0x138: "number of yuri radar",
    0x144: "somthing to do with industrial plant",
    0x148: "somthing to do with industrial plant",
    0x14c: "somthing to do with industrial plant",
    0x150: "somthing to do with industrial plant (activates the bonus? 1 = active, 0 = not active)",
    0x158: "Miners",
    0x15c: "Ore refinerys",
    0x160: "War Factorys",

    0x164: "InfantrySelfHeal",
    0x168: "UnitsSelfHeal",
    0x1ed: "IsInPlayerControl", ##TODO make sure
    0x1f6: "IsGameOver",
    0x1f7: "ISWINNEROFFSET",
    0x1f8: "ISLOSEROFFSET",

    0x1fc: "not sure about this one changed when made allied engi but only for the first one",
    0x240: "spysat? when i made it it went from 0->256",
    0x244: "not sure about this one changed when made allied engi but only for the first one",


#TODO this is the spot that has DECLARE_PROPERTY(DynamicVectorClass<SuperClass*>, Supers);
    0x26c: "Structure just placed (9 = tesla reactor, 10 = sov battle lab, 11 = soviet barracks, 13 = soviet radar, 14 = sov WF, 15 = soviet Ore ref, 16 = sov wall, 20 = sentry gun, 24 = iron certain26 = sov service depot, 25 = soviet construction vehicle, 53 = tesla coil, 54 = Nuke, 65 = nuke power plant, 67 = flak track, 310 = industrial plant, 359 = battle bunker)",
    0x270: "Infantry unit just made (1 = conscript, 2 = Tesla Trooper, 7 = Crazy Ivan, 8 = deso, 9 = soviet dog, 25 = falk trooper,27 = soviet Engi, 48 = Boris, )",
    0x274: "vehicle just made (1 = sov war miner, 2 = apoc, 3 = rhino tank, 14 = v3 rocket launcher, 15 = kirov, 16 = Terror drone, 17 = flak track, 26 = Sov mcv67 = siege chopper, )",
    0x278: "aircraft just made", # TODO this is swapped with vehicle in the houseClass.h

#     DECLARE_PROPERTY(CDTimerClass, RepairTimer); // for AI
# DECLARE_PROPERTY(CDTimerClass, AlertTimer);
# DECLARE_PROPERTY(CDTimerClass, BorrowedTime);
# DECLARE_PROPERTY(CDTimerClass, PowerBlackoutTimer);
    0x2a4: "something to do with force shield",
    0x2a8: "something to do with force shield",
    0x2ac: "something to do with force shield",
# DECLARE_PROPERTY(CDTimerClass, RadarBlackoutTimer);




0x2bc: "Yuri battle lab inflitrated (1=yes 0=no)",
0x2bd:"Soviet battle lab inflitrated (1=yes 0=no)",
0x2be: "Allied battle lab inflitrated (1=yes 0=no)",
0x2bf:                 "BarracksInfiltrated (0 if not)",
0x2c0:                "WarFactoryInfiltrated (0 if not)",



    0x2d4: "airport docs (numebr of aircrafts that can be built)",
    0x2d8: "Robot tanks online = 1, offline = 0",
    0x2dc: "Credits spent",
    0x2e0: "HarvestedCredits",
    0x2e4: "StolenBuildingsCredits",


    0x2e8: "number of vehicles And navy?", ## TODO make sure this is also navy
    0x2ec: "number of Naval units",
    0x2f0: "Number of structures (Even ones just in que and not ready. will go back down if cancelled)",
    0x2f4: "Amount of infantry",
    0x2f8: "aircraft count",

    0x30c: "Balance",


    0x32c: "Total amount of Harriers made",
    0x340: "goes up by 1 when there is a paradrop plane (keeps going up every paradrop)",
    0x344: "Total amount of Black eagles made",
    0x350: "amount of spy planes made",

    0xb30: "Total amount of GI made",
    0xb34: "Total amount of Conscript made",
    0xb38: "Total amount of Tesla Trooper made",
    0xb3c: "Total amount of Allied Engineer made",
    0xb40: "Total amount of Rocketeer made",
    0xb44: "Total amount of Navy SEAL made",
    0xb48: "Total amount of Yuri Clone made",
    0xb4c: "Total amount of Crazy Ivan made",
    0xb50: "Total amount of Desolator made",
    0xb54: "Total amount of Soviet Dog made",
    0xb6c: "Total amount of Chrono Legionnaire made",
    0xb70: "Total amount of Spy made",
    0xb80: "Total amount of Yuri Prime made",
    0xb84: "Total amount of Sniper made",
    0xb90: "Total amount of Tanya made",
    0xb94: "Total amount of Flak Trooper made",
    0xb98: "Total amount of Terrorist made",
    0xb9c: "Total amount of Soviet Engineer made",
    0xba0: "Total amount of Allied Dog made",
    0xbe4: "Total amount of Yuri Engineer made",
    0xbe8: "Total amount of Guardian GI (GGI) made",
    0xbec: "Total amount of Initiate made",
    0xbf0: "Total amount of Boris made",
    0xbf4: "Total amount of Brute made",
    0xbf8: "Total amount of Virus made",

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

    #TODO missing the aircraft lost here

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

    #0x5378: "num of airpads",
    0x537c: "Barracks count",
    0x5380: "war factorys?",
    0x5384: "Construction Yard count",
    #0x5388: "num of shipyards",
    #0x0x538c: "num of ore purifiers",

    0x53a4: "Power output",
    0x53a8: "power drain",

0x53ac: "aircraft factory pointer offset",

0x53b0: "Unit factory pointer offset",


    #this si where the primary things are! like primary WF

    0x53b4: "tank being built? 0 when no example when yes 47618368",
    0x53bc: "when i click a structure this goes super high and back to 0 when i cancel or place (what is being built??) (BLOCKED)",
    0x53e4: "infantry lost",
    0x5434: "infantry lost",
    0x5438: "number of buildings lost",
    0x5488: "number of buildings lost",
    0x5490: "(changes to huge number when undeployed and 0 when deployed) (Also changes to a huge number when placing tesla reactor and selling reactor as well). (then i blocked it)",
    0x54d8: " keeps going up the more i destroy my own buildings 176669 -> 176696",
    0x54e8: "goes up by 200 every miner dump (Ignored)",
    0x5510: "Number of structures (Even ones just in que and not ready. will go back down if cancelled)",
    0x5524: "vehicle count?",
    0x552c: "went 0 -> 285645296 when i sold tesla reactor (Blocked)",
    0x5530: "went 0 -> 11 when i sold tesla reactor",
    0x5534: "went 1 -> 257 when i sold tesla reactor",
    0x5538: "infantry count",
    0x5560: "Number of structures currently has",
    0x5574: "number of vehicles",

0x5554:"BUILDINGOFFSET",
0x5568:"TANKOFFSET",
    0x557c: "INFOFFSET",
0x5590:"AIRCRAFTOFFSET",


0x55A4: "Total made Buildings Offset",
0x55B8: "Total made Tanks Offset",
0x55CC: "Total made Inf Offset",
0x55E0: "Total made Aircraft Offset",






    0x5588: "infantry count",
    0x55a4: "went from 0 to super high when i placed tesla reactor (283261376) (BLOCKED)",
    0x55a8: "goes up the more structures you have? not linear",
    0x55ac: "went from 1 to 257 when i placed tesla reactor",
    0x55b0: "total amount of structures placed",
    0x55d8: "Infantry count???? when i killed sov barracks 79020 -> 144567",



    0x5724: "went 49918736 -> 259478592 when i placed tesla reactor (BLOCKED)",
    0x5728: "went 20 -> 30 when i placed tesla reactor. 30 -> 50 when i placed second tesla reactor (BLOCKED)",
    0x5730: "deploying soviet mcv makes this 20, undeploying makes this 0. then i placed a tesla reactor and it turned 30 selling made it 20 again (then i blocked it)",
    0x5758: "went 25 -> 21 when i placed second tesla reactor (BLOCKED)",
    0x575c: "went 9 -> 11 when i placed tesla reactor. 6 -> 9 when i placed second tesla reactor (BLOCKED)",
    0x5760: "went 6 -> 10 when i placed tesla reactor. 10 -> 14 when i placed second tesla reactor (BLOCKED)",
    0x5778: "when soviet barracks got destroyed: 257 -> 0",
    0x57a4: "Adds around 360 every second (Game time?)",
    0x57a8: "scrolling around the map???",
    0x57bc: "keeps going up when you low power example size jump: 395159 -> 395726",
    0x1602a: "player name",
    0x16054: "color scheme",
    0x160a8: "money spent on infantry",
    0x160ac: "money spent on tanks",
    #0x160b0: "TotalOwnedAircraftCost",
    #0x160b4: "PowerSurplus",
# this is the last address no point in going beyond this
}

IGNORED_OFFSETS = [0x54e8, 0x57a4, 0x57a8, 0x5730, 0x5490, 0x552c, 0x53bc, 0x55a4, 0x5724, 0x5728, 0x5760,
                   0x5758, 0x5498, 0x5754, 0x557c, 0x32f4c, 0x1b86c, 0x510dc, 0x1ce54, 0xac05c, 0xac060, 0xac668,
                   0xac784, 0xac788, 0xacd90, 0xaceac, 0xaceb0, 0xad4b8, 0xac5d4, 0xac5d8, 0xac5f0, 0xac5f4, 0xaccfc,
                   0xacd00, 0xacd18, 0xacd1c, 0xace80, 0xad424, 0xad428, 0xad440, 0xad444, 0x1706c, 0x1ce84, 0x17070,
                   0x1ce88, 0x175e8
    , 0x17604, 0x17600, 0x175e4, 0x2e72c, 0x2e730, 0x34584, 0x2eca8, 0x2ecc4, 0x56d98, 0x56ce0, 0x56cdc, 0x52ef4,
                   0x52ac8, 0x524bc, 0x51d94, 0x56da0, 0x56ce8, 0x52ef8, 0x524c0, 0x51d98, 0x56d10, 0x56d18, 0x56d14,
                   0x56d1c
    , 0x56d20, 0x56d24, 0x56d80, 0x56d18, 0x56d10, 0x56fa8, 0x56d88, 0x56fa0, 0x56fa4, 0x56fac, 0x52310, 0x5232c,
                   0x52a38, 0x52a54, 0x53470, 0x5348c, 0x47434, 0x47458, 0x4745c, 0x57114, 0x572dc, 0xa208c, 0xa27b4,
                   0xa2090, 0xa27b8
                   ]

MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff
SCAN_SIZE = 0x30
START_OFFSET = 0x2ac  # Variable to control how far ahead the scan startsSCAN_SIZE = 0x10000

SIZE_TO_READ = 1


class GameData:
    def __init__(self):
        self.balance = [0] * MAXPLAYERS
        self.validPlayer = [False] * MAXPLAYERS
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
    if ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytesRead)):
        return buffer.raw
    else:
        raise ctypes.WinError()


def scan_memory_changes(process_handle, realClassBase, prev_snapshot):
    current_snapshot = []
    changes = []

    # Iterate over the range starting from realClassBase + START_OFFSET
    for offset in range(START_OFFSET, START_OFFSET + SCAN_SIZE, SIZE_TO_READ):
        address = realClassBase + offset
        try:
            raw = read_process_memory(process_handle, address, SIZE_TO_READ)

            if SIZE_TO_READ == 1:
                current_value = raw[0]  # interpret as single byte (unsigned)
            elif SIZE_TO_READ == 2:
                current_value = int.from_bytes(raw, byteorder='little', signed=False)
            elif SIZE_TO_READ == 4:
                current_value = int.from_bytes(raw, byteorder='little', signed=False)
            else:
                # optionally support signed or larger types
                current_value = int.from_bytes(raw, byteorder='little', signed=False)

            current_snapshot.append(current_value)

            # Skip processing if the offset is in the ignored list
            if offset in IGNORED_OFFSETS:
                continue

            # If this is not the first snapshot, compare with the previous snapshot
            if prev_snapshot is not None:
                prev_value = prev_snapshot[(offset - START_OFFSET) // SIZE_TO_READ]
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
    CBA = ctypes.c_uint32.from_buffer_copy(read_process_memory(process_handle, classBaseArrayPtr, 4)).value

    classbasearray = fixedPointValue + 1120 * 4

    # A flag to track if any changes were detected during the scan
    any_changes = False

    for i in range(MAXPLAYERS):
        classBasePtr = ctypes.c_uint32.from_buffer_copy(read_process_memory(process_handle, classbasearray, 4)).value
        classbasearray += 4
        if classBasePtr != INVALIDCLASS:
            game_data.validPlayer[i] = True
            realClassBasePtr = classBasePtr * 4 + CBA
            realClassBase = ctypes.c_uint32.from_buffer_copy(
                read_process_memory(process_handle, realClassBasePtr, 4)).value

            # Initialize or update the memory snapshot
            prev_snapshot = game_data.memorySnapshot[i] if game_data.memorySnapshot[i] is not None else None
            current_snapshot, changes = scan_memory_changes(process_handle, realClassBase, prev_snapshot)
            game_data.memorySnapshot[i] = current_snapshot

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
