import ctypes
import logging
import traceback

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox

# Constants
MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff

# Memory offsets
BALANCEOFFSET = 0x30c
CREDITSPENT_OFFSET = 0x2dc
USERNAMEOFFSET = 0x1602a
ISWINNEROFFSET = 0x1f7
ISLOSEROFFSET = 0x1f8
POWEROUTPUTOFFSET = 0x53a4
POWERDRAINOFFSET = 0x53a8
HOUSETYPECLASSBASEOFFSET = 0x34
COUNTRYSTRINGOFFSET = 0x24
COLORSCHEMEOFFSET = 0x16054

# Process name
PROCESS_NAME = "gamemd-spawn.exe"


def read_process_memory(process_handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t()
    try:
        success = ctypes.windll.kernel32.ReadProcessMemory(
            process_handle, address, buffer, size, ctypes.byref(bytesRead)
        )
        if success:
            return buffer.raw
        else:
            error_code = ctypes.windll.kernel32.GetLastError()
            if error_code == 299:  # ERROR_PARTIAL_COPY
                logging.warning("Memory read incomplete. Game might still be loading.")
                return None
            elif error_code in (5, 6):  # ERROR_ACCESS_DENIED or ERROR_INVALID_HANDLE
                logging.error("Failed to read memory: Process might have exited.")
                raise Exception("Process has exited.")
            else:
                logging.error(f"Failed to read memory: Error code {error_code}")
                raise Exception("Process has exited.")
    except Exception as e:
        logging.error(f"Exception in read_process_memory: {e}")
        raise Exception("Process has exited.")


def safe_write_int(process_handle, address, value):
    data = value.to_bytes(4, byteorder='little')
    bytesWritten = ctypes.c_size_t()
    success = ctypes.windll.kernel32.WriteProcessMemory(
        process_handle, address, data, 4, ctypes.byref(bytesWritten)
    )
    if not success:
        error_code = ctypes.windll.kernel32.GetLastError()
        logging.error(f"Failed to write memory at {address}, error code: {error_code}")


def detect_if_all_players_are_loaded(process_handle):
    """
    Uses a robust check system to verify if players are fully loaded.
    Returns True if at least one player is found to be initialized.
    """
    try:
        fixedPoint = 0xa8b230
        classBaseArrayPtr = 0xa8022c

        fixedPointData = read_process_memory(process_handle, fixedPoint, 4)
        if fixedPointData is None:
            logging.error("Failed to read memory at fixedPoint.")
            return False

        fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointData).value
        classBaseArrayData = read_process_memory(process_handle, classBaseArrayPtr, 4)
        if classBaseArrayData is None:
            return False
        classBaseArray = ctypes.c_uint32.from_buffer_copy(classBaseArrayData).value
        classBasePlayer = fixedPointValue + 1120 * 4

        # Loop through potential player slots
        for i in range(MAXPLAYERS):
            player_data = read_process_memory(process_handle, classBasePlayer, 4)
            classBasePlayer += 4
            if player_data is None:
                logging.warning(f"Skipping Player {i} due to incomplete memory read.")
                continue

            classBasePtr = ctypes.c_uint32.from_buffer_copy(player_data).value
            if classBasePtr == INVALIDCLASS:
                logging.info(f"Skipping Player {i} as not fully initialized yet.")
                continue

            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)
            if realClassBaseData is None:
                continue

            realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBaseData).value

            loaded = 0
            # Check some fixed offsets for expected values
            right_values = {0x551c: 66, 0x5778: 0, 0x57ac: 90}
            for offset, value in right_values.items():
                ptr = realClassBase + offset
                data = read_process_memory(process_handle, ptr, 4)
                if data and int.from_bytes(data, byteorder='little') == value:
                    loaded += 1

            if loaded >= 2:
                logging.info("Players loaded. Proceeding with players initialization.")
                return True
        return False

    except Exception as e:
        logging.error(f"Exception in detect_if_all_players_are_loaded: {e}")
        traceback.print_exc()
        return False


class Player:
    def __init__(self, index, process_handle, real_class_base):
        self.index = index
        self.process_handle = process_handle
        self.real_class_base = real_class_base

    def set_money(self, amount):
        """Sets the player's money to the given amount."""
        balance_ptr = self.real_class_base + BALANCEOFFSET
        safe_write_int(self.process_handle, balance_ptr, amount)


class GameData:
    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def clear_players(self):
        self.players.clear()


def initialize_players_after_loading(game_data, process_handle):
    """
    Initializes the players from memory once they are loaded.
    Returns the number of valid players found.
    """
    game_data.clear_players()
    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c

    fixedPointData = read_process_memory(process_handle, fixedPoint, 4)
    if fixedPointData is None:
        logging.error("Failed to read memory at fixedPoint.")
        return 0

    fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointData).value
    classBaseArrayData = read_process_memory(process_handle, classBaseArrayPtr, 4)
    if classBaseArrayData is None:
        return 0
    classBaseArray = ctypes.c_uint32.from_buffer_copy(classBaseArrayData).value
    classbasearray = fixedPointValue + 1120 * 4
    valid_player_count = 0

    for i in range(MAXPLAYERS):
        memory_data = read_process_memory(process_handle, classbasearray, 4)
        classbasearray += 4

        if memory_data is None:
            logging.warning(f"Skipping player {i} due to incomplete memory read.")
            continue

        classBasePtr = ctypes.c_uint32.from_buffer_copy(memory_data).value
        if classBasePtr != INVALIDCLASS:
            valid_player_count += 1
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)

            if realClassBaseData is None:
                logging.warning(f"Skipping player {i} due to incomplete real class base read.")
                continue

            realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBaseData).value
            player = Player(i + 1, process_handle, realClassBase)
            game_data.add_player(player)
    logging.info(f"Number of valid players: {valid_player_count}")
    return valid_player_count


def get_process_handle(process_name):
    try:
        import pymem
        pm = pymem.Pymem(process_name)
        return pm.process_handle
    except Exception as e:
        logging.error(f"Failed to get process handle: {e}")
        return None


# PySide6 UI with a single "Give Money" button
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Give Money")
        layout = QVBoxLayout()
        self.button = QPushButton("Give Money")
        self.button.clicked.connect(self.give_money)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def give_money(self):
        process_handle = get_process_handle(PROCESS_NAME)
        if process_handle is None:
            QMessageBox.critical(self, "Error", "Game process not found.")
            return

        if not detect_if_all_players_are_loaded(process_handle):
            QMessageBox.critical(self, "Error", "Players are not fully loaded yet.")
            return

        game_data = GameData()
        valid_count = initialize_players_after_loading(game_data, process_handle)
        if valid_count == 0:
            QMessageBox.critical(self, "Error", "No valid players found.")
            return

        for player in game_data.players:
            player.set_money(100000)

        QMessageBox.information(self, "Success", "Money set to 100,000.")


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
