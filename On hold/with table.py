import pymem
import time
import ctypes
from ctypes import Structure, c_int32, c_uint8, c_uint32, c_wchar
import pandas as pd
import tkinter as tk
from tkinter import ttk

MAXPLAYERS = 8
PROCESS_NAME = "gamemd-spawn.exe"

# Offsets
BALANCEOFFSET = 0x30c
CREDITSPENT_OFFSET = 0x2dc
USERNAMEOFFSET = 0x1602a
ISWINNEROFFSET = 0x1f7
ISLOSEROFFSET = 0x1f8
POWEROUTPUTOFFSET = 0x53a4
POWERDRAINOFFSET = 0x53a8
HOUSETYPECLASSBASEOFFSET = 0x34
COUNTRYSTRINGOFFSET = 0x24
COLOROFFSET = 0x56fC
COLORSCHEMEOFFSET = 0x16054
BUILDINGOFFSET = 0x5554
INFOFFSET = 0x557c
TANKOFFSET = 0x5568


class ColorStruct(Structure):
    _fields_ = [("rgb", c_uint8 * 3)]


class InfantryUnits(Structure):
    _fields_ = [
        ("giCount", c_int32),
        ("conscriptCount", c_int32),
        ("teslaTrooperCount", c_int32),
        ("alliedEngiCount", c_int32),
        ("rocketeerCount", c_int32),
        ("sealCount", c_int32),
        ("g", c_int32),
        ("crazyIvanCount", c_int32),
        ("desolatorCount", c_int32),
        ("sovDogCount", c_int32),
        ("k", c_int32),
        ("l", c_int32),
        ("m", c_int32),
        ("n", c_int32),
        ("o", c_int32),
        ("chronoCount", c_int32),
        ("spyCount", c_int32),
        ("r", c_int32),
        ("psiCommandoCount", c_int32),
        ("t", c_int32),
        ("u", c_int32),
        ("alliedSniperCount", c_int32),
        ("w", c_int32),
        ("x", c_int32),
        ("tanyaCount", c_int32),
        ("flakTrooperCount", c_int32),
        ("a1", c_int32),
        ("sovEngiCount", c_int32),
        ("alliedDogCount", c_int32),
        ("b1", c_int32),
        ("b2", c_int32),
        ("b3", c_int32),
        ("b4", c_int32),
        ("b5", c_int32),
        ("b6", c_int32),
        ("b7", c_int32),
    ]


class TankUnits(Structure):
    _fields_ = [
        ("allMcvCount", c_int32),
        ("sovMinerCount", c_int32),
        ("apocCount", c_int32),
        ("rhinoCount", c_int32),
        ("sovAmphibiousTransportCount", c_int32),
        ("f", c_int32),
        ("g", c_int32),
        ("h", c_int32),
        ("i", c_int32),
        ("grizzyCount", c_int32),
        ("k", c_int32),
        ("l", c_int32),
        ("m", c_int32),
        ("aircraftCarrierCount", c_int32),
        ("v3Count", c_int32),
        ("kirovCount", c_int32),
        ("sovDroneCount", c_int32),
        ("flakTrakCount", c_int32),
        ("destroyerCount", c_int32),
        ("submarineCount", c_int32),
        ("aigesCruzerCount", c_int32),
        ("alliedAmphibiousTransportCount", c_int32),
        ("dreadnoughtCount", c_int32),
        ("nightHawkCount", c_int32),
        ("squidCount", c_int32),
        ("dolphinCount", c_int32),
        ("a1", c_int32),
        ("tankDestroyerCount", c_int32),
        ("a3", c_int32),
        ("teslaTankCount", c_int32),
        ("b2", c_int32),
        ("b3", c_int32),
        ("b4", c_int32),
        ("alliedMinerCount", c_int32),
        ("prismTankCount", c_int32),
        ("b7", c_int32),
        ("seaScorpionCount", c_int32),
        ("mirageTankCount", c_int32),
        ("ifvCount", c_int32),
    ] + [("v" + str(i), c_int32) for i in range(39, 50)] + [
        ("x5", c_int32 * 10),
        ("x6", c_int32 * 10),
        ("v70", c_int32),
        ("v71", c_int32),
        ("robotTankCount", c_int32),
    ]


class Buildings(Structure):
    _fields_ = [
        ("alliedPowerPlantCount", c_int32),
        ("alliedRefinery", c_int32),
        ("alliedMcvCount", c_int32),
        ("alliedBarrackCount", c_int32),
        ("e", c_int32),
        ("alliedServiceDepot", c_int32),
        ("alliedLab", c_int32),
        ("alliedWarFactory", c_int32),
        ("i", c_int32),
        ("sovPowerPlant", c_int32),
        ("sovBattleLab", c_int32),
        ("sovBarracks", c_int32),
        ("m", c_int32),
        ("sovRadar", c_int32),
        ("sovWarFactory", c_int32),
        ("sovRefinery", c_int32),
        ("q", c_int32),
        ("r", c_int32),
        ("yuriRadar", c_int32),
        ("t", c_int32),
        ("sovSentryCount", c_int32),
        ("patriotMissile", c_int32),
        ("w", c_int32),
        ("alliedNavalYard", c_int32),
        ("sovIronCurtainCount", c_int32),
        ("sovMcvCount", c_int32),
        ("sovServiceDepot", c_int32),
        ("chronosphereCount", c_int32),
        ("a3", c_int32),
        ("weatherStormCount", c_int32),
    ] + [("b" + str(i), c_int32) for i in range(2, 11)]


def read_wstring(pm, address, max_length=1024):
    buffer = ctypes.create_string_buffer(max_length)
    bytes_read = ctypes.c_size_t()
    ctypes.windll.kernel32.ReadProcessMemory(
        pm.process_handle, ctypes.c_void_p(address),
        buffer, max_length, ctypes.byref(bytes_read)
    )
    return buffer.raw.decode('utf-16-le').rstrip('\x00')


def safe_read_uint(pm, address):
    try:
        return pm.read_uint(address)
    except:
        return 0


def safe_read_int(pm, address):
    try:
        return pm.read_int(address)
    except:
        return 0


def safe_read_bool(pm, address):
    try:
        return pm.read_bool(address)
    except:
        return False


def read_game_data():
    pm = pymem.Pymem(PROCESS_NAME)

    fixed_point = safe_read_uint(pm, 0xa8b230)
    class_base_array = safe_read_uint(pm, 0xa8022c)

    if fixed_point == 0 or class_base_array == 0:
        return []

    player_data = []

    for i in range(MAXPLAYERS):
        class_base_ptr = safe_read_uint(pm, fixed_point + 1120 * 4 + i * 4)

        if class_base_ptr != 0xffffffff and class_base_ptr != 0:
            real_class_base_ptr = class_base_ptr * 4 + class_base_array
            real_class_base = safe_read_uint(pm, real_class_base_ptr)

            if real_class_base == 0:
                continue

            balance = safe_read_int(pm, real_class_base + BALANCEOFFSET)
            spent_credit = safe_read_int(pm, real_class_base + CREDITSPENT_OFFSET)
            username = read_wstring(pm, real_class_base + USERNAMEOFFSET, 32)
            is_winner = safe_read_bool(pm, real_class_base + ISWINNEROFFSET)
            is_loser = safe_read_bool(pm, real_class_base + ISLOSEROFFSET)
            power_output = safe_read_int(pm, real_class_base + POWEROUTPUTOFFSET)
            power_drain = safe_read_int(pm, real_class_base + POWERDRAINOFFSET)

            house_type_class_base = safe_read_uint(pm, real_class_base + HOUSETYPECLASSBASEOFFSET)
            country_name = read_wstring(pm, safe_read_uint(pm, house_type_class_base + COUNTRYSTRINGOFFSET), 64)

            color_ptr = house_type_class_base + COLOROFFSET
            color = ColorStruct.from_buffer_copy(pm.read_bytes(color_ptr, ctypes.sizeof(ColorStruct)))

            color_scheme = safe_read_uint(pm, real_class_base + COLORSCHEMEOFFSET)

            infantry_ptr = safe_read_uint(pm, real_class_base + INFOFFSET)
            tanks_ptr = safe_read_uint(pm, real_class_base + TANKOFFSET)
            buildings_ptr = safe_read_uint(pm, real_class_base + BUILDINGOFFSET)

            infantry = InfantryUnits.from_buffer_copy(pm.read_bytes(infantry_ptr, ctypes.sizeof(InfantryUnits)))
            tanks = TankUnits.from_buffer_copy(pm.read_bytes(tanks_ptr, ctypes.sizeof(TankUnits)))
            buildings = Buildings.from_buffer_copy(pm.read_bytes(buildings_ptr, ctypes.sizeof(Buildings)))

            player_data.append({
                "username": username,
                "balance": balance,
                "spent_credit": spent_credit,
                "is_winner": is_winner,
                "is_loser": is_loser,
                "power_output": power_output,
                "power_drain": power_drain,
                "country_name": country_name,
                "color": color.rgb,
                "color_scheme": color_scheme,
                "infantry": infantry,
                "tanks": tanks,
                "buildings": buildings
            })

    return player_data


def display_table(data):
    root = tk.Tk()
    root.title("Game Data")

    # Create a frame for the table
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    # Create a treeview widget
    tree = ttk.Treeview(frame)
    tree.pack(fill=tk.BOTH, expand=True)

    # Define columns
    columns = ["username", "balance", "spent_credit", "is_winner", "is_loser", "power_output", "power_drain", "country_name", "color", "color_scheme"]
    tree["columns"] = columns

    # Define column headings
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    # Insert data into the table
    for i, player in enumerate(data):
        tree.insert("", "end", values=(
            player["username"], player["balance"], player["spent_credit"], player["is_winner"], player["is_loser"],
            player["power_output"], player["power_drain"], player["country_name"],
            f"RGB({player['color'][0]}, {player['color'][1]}, {player['color'][2]})", player["color_scheme"]
        ))

    # Start the GUI loop
    root.mainloop()


if __name__ == "__main__":
    while True:
        try:
            game_data = read_game_data()
            if game_data:
                display_table(game_data)
            else:
                print("No valid player data found.")
        except pymem.exception.ProcessNotFound:
            print("Game not running. Waiting...")
        except Exception as e:
            print(f"An error occurred: {e}")
        time.sleep(5)
