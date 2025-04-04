import ctypes
import psutil
import tkinter as tk
from tkinter import ttk, messagebox
from ctypes import wintypes

# --- Constants and Globals ---
DEFAULT_SCAN_SIZE = 0x200  # Default scan size in bytes (512 bytes)
STRING_READ_SIZE = 32  # Fallback number of bytes to read when in "String" mode
MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff
RANDOMPTROFFSET = 0x53b4  # This pointer offset may change over time

# Offsets used for pointer chasing (from your original code)
FIXED_POINT_ADDR = 0xa8b230
CLASS_BASE_ARRAY_PTR = 0xa8022c

# Windows process access flags for OpenProcess
PROCESS_ALL_ACCESS = (0x0010 | 0x0020 | 0x0008 | 0x0010)


# --- Memory Functions ---

def find_pid_by_name(name):
    """Return the PID for the process with the given name."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None


def read_process_memory(process_handle, address, size):
    """
    Read 'size' bytes from the target process at 'address'.
    Returns raw bytes if successful, or None if not.
    """
    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t()
    try:
        if ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytesRead)):
            return buffer.raw
        else:
            raise ctypes.WinError()
    except OSError as e:
        # WinError 299 means only part of the memory could be read
        if hasattr(e, 'winerror') and e.winerror == 299:
            return None
        else:
            raise


def get_dynamic_unit_array_base():
    """
    Recalculate the pointer using your pointer-chasing logic.
    This function follows the pointer chain and reads the 4-byte value at (realClassBase + RANDOMPTROFFSET).
    Returns the unit array base pointer if successful, or None.
    """
    pid = find_pid_by_name("gamemd-spawn.exe")
    if pid is None:
        return None
    process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    try:
        fixedPointValue_raw = read_process_memory(process_handle, FIXED_POINT_ADDR, 4)
        if fixedPointValue_raw is None:
            return None
        fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointValue_raw).value

        classBaseArray_raw = read_process_memory(process_handle, CLASS_BASE_ARRAY_PTR, 4)
        if classBaseArray_raw is None:
            return None
        classBaseArray = ctypes.c_uint32.from_buffer_copy(classBaseArray_raw).value

        # Compute starting pointer as in your original code.
        classbasearray = fixedPointValue + 1120 * 4

        for i in range(MAXPLAYERS):
            ptr_raw = read_process_memory(process_handle, classbasearray, 4)
            classbasearray += 4
            if ptr_raw is None:
                continue
            classBasePtr = ctypes.c_uint32.from_buffer_copy(ptr_raw).value
            if classBasePtr != INVALIDCLASS:
                realClassBasePtr = classBasePtr * 4 + classBaseArray
                realClassBase_raw = read_process_memory(process_handle, realClassBasePtr, 4)
                if realClassBase_raw is None:
                    continue
                realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBase_raw).value
                unit_ptr_address = realClassBase + RANDOMPTROFFSET
                unit_array_base_raw = read_process_memory(process_handle, unit_ptr_address, 4)
                if unit_array_base_raw is None:
                    continue
                unit_array_base = ctypes.c_uint32.from_buffer_copy(unit_array_base_raw).value
                return unit_array_base
    finally:
        ctypes.windll.kernel32.CloseHandle(process_handle)
    return None


def read_memory_block(process_handle, start_address, total_size, step, mode):
    """
    Read a block of memory from start_address for total_size bytes in increments of 'step'.
    'mode' should be one of "byte", "int", or "string".
    For "string" mode the block is decoded as ASCII.
    Returns a list of tuples: (offset, absolute_address, value, hex_value)
    """
    data = []
    for offset in range(0, total_size, step):
        address = start_address + offset
        raw = read_process_memory(process_handle, address, step)
        if raw is None:
            value = "N/A"
            hex_value = "N/A"
        else:
            if mode in ("byte", "int"):
                val_int = int.from_bytes(raw, byteorder='little')
                value = val_int
                hex_value = hex(val_int)
            elif mode == "string":
                try:
                    value = raw.decode("ascii", errors="replace").strip('\x00')
                    hex_value = raw.hex()
                except Exception:
                    value = "DecodeError"
                    hex_value = "DecodeError"
        data.append((offset, address, value, hex_value))
    return data


# --- Dynamic Pointer Viewer Window ---

class DynamicPointerWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dynamic Pointer Viewer")
        self.geometry("400x150")

        # Label to display the current dynamic pointer value.
        self.pointer_label = ttk.Label(self, text="Dynamic Pointer: ", font=("Arial", 14))
        self.pointer_label.pack(pady=20)

        # Button to open the manual scanner window.
        open_scanner_btn = ttk.Button(self, text="Open Manual Scanner", command=self.open_manual_scanner)
        open_scanner_btn.pack(pady=10)

        # Start auto-refreshing the pointer.
        self.auto_refresh()

    def auto_refresh(self):
        """Re-read the dynamic pointer and update the label every 500 ms."""
        ptr = get_dynamic_unit_array_base()
        if ptr is not None:
            self.pointer_label.config(text=f"Dynamic Pointer: {hex(ptr)}")
        else:
            self.pointer_label.config(text="Dynamic Pointer: Process not found or read error")
        self.after(500, self.auto_refresh)

    def open_manual_scanner(self):
        """Open the Manual Memory Scanner window."""
        ManualScannerWindow(self)


# --- Manual Memory Scanner Window ---

class ManualScannerWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Manual Memory Scanner")
        self.geometry("800x600")

        # Variables for user inputs.
        default_ptr = get_dynamic_unit_array_base()
        self.base_address_var = tk.StringVar(value=hex(default_ptr) if default_ptr is not None else "0x0")
        self.extra_before_var = tk.StringVar(value="0")
        self.extra_after_var = tk.StringVar(value="0")
        self.read_mode = tk.StringVar(value="int")  # possible values: "byte", "int", "string"
        self.string_size_var = tk.StringVar(value="32")

        # Dictionary to store previous scan values (keyed by offset) for change detection.
        self.previous_values = {}

        self.create_widgets()
        self.auto_refresh()

    def create_widgets(self):
        # --- Top Frame for Memory Address and Extra Offsets ---
        top_frame = ttk.Frame(self)
        top_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(top_frame, text="Memory Base Address:").grid(row=0, column=0, sticky="w")
        base_entry = ttk.Entry(top_frame, textvariable=self.base_address_var, width=20)
        base_entry.grid(row=0, column=1, sticky="w", padx=(5, 20))

        ttk.Label(top_frame, text="Extra Before (bytes):").grid(row=0, column=2, sticky="w")
        before_entry = ttk.Entry(top_frame, textvariable=self.extra_before_var, width=10)
        before_entry.grid(row=0, column=3, sticky="w", padx=(5, 20))

        ttk.Label(top_frame, text="Extra After (bytes):").grid(row=0, column=4, sticky="w")
        after_entry = ttk.Entry(top_frame, textvariable=self.extra_after_var, width=10)
        after_entry.grid(row=0, column=5, sticky="w", padx=(5, 20))

        # --- Options Frame for Read Mode, String Size, Scan and Copy Buttons ---
        options_frame = ttk.Frame(self)
        options_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(options_frame, text="View Mode:").pack(side="left")
        ttk.Radiobutton(options_frame, text="1 Byte", variable=self.read_mode, value="byte").pack(side="left", padx=5)
        ttk.Radiobutton(options_frame, text="4 Byte", variable=self.read_mode, value="int").pack(side="left", padx=5)
        ttk.Radiobutton(options_frame, text="String", variable=self.read_mode, value="string").pack(side="left", padx=5)

        # String size textbox (enabled only in "string" mode)
        self.string_size_label = ttk.Label(options_frame, text="String Size:")
        self.string_size_entry = ttk.Entry(options_frame, textvariable=self.string_size_var, width=5)
        self.string_size_label.pack(side="left", padx=5)
        self.string_size_entry.pack(side="left", padx=5)

        # Function to update the state of the string size textbox.
        def update_string_size_state(*args):
            if self.read_mode.get() == "string":
                self.string_size_entry.state(["!disabled"])
                self.string_size_label.state(["!disabled"])
            else:
                self.string_size_entry.state(["disabled"])
                self.string_size_label.state(["disabled"])

        self.read_mode.trace("w", update_string_size_state)
        update_string_size_state()  # call initially

        scan_button = ttk.Button(options_frame, text="Scan Memory", command=self.scan_memory)
        scan_button.pack(side="left", padx=20)

        copy_button = ttk.Button(options_frame, text="Copy Selected", command=self.copy_selected)
        copy_button.pack(side="left", padx=5)

        # --- Frame for the Treeview with Scrollbar ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Create Treeview with four columns: Offset, Absolute Address, Value, Hex Value
        self.tree = ttk.Treeview(tree_frame, columns=("offset", "address", "value", "value_hex"), show="headings")
        self.tree.heading("offset", text="Offset")
        self.tree.heading("address", text="Absolute Address")
        self.tree.heading("value", text="Value")
        self.tree.heading("value_hex", text="Hex Value")
        self.tree.column("offset", width=80, anchor="center")
        self.tree.column("address", width=150, anchor="center")
        self.tree.column("value", width=200, anchor="center")
        self.tree.column("value_hex", width=150, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        # Configure a tag for changed rows.
        self.tree.tag_configure("changed", background="red")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def scan_memory(self):
        # Clear previous entries.
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            base_address = int(self.base_address_var.get(), 16)
        except ValueError:
            self.tree.insert("", "end", values=("Invalid base address", "", "", ""))
            return

        try:
            extra_before = int(self.extra_before_var.get())
            extra_after = int(self.extra_after_var.get())
        except ValueError:
            self.tree.insert("", "end", values=("Invalid extra before/after", "", "", ""))
            return

        start_address = base_address - extra_before
        total_size = extra_before + DEFAULT_SCAN_SIZE + extra_after

        mode = self.read_mode.get()
        if mode == "byte":
            step = 1
        elif mode == "int":
            step = 4
        elif mode == "string":
            try:
                step = int(self.string_size_var.get())
            except ValueError:
                step = STRING_READ_SIZE  # fallback
        else:
            step = 4

        pid = find_pid_by_name("gamemd-spawn.exe")
        if pid is None:
            self.tree.insert("", "end", values=("Process not found", "", "", ""))
            return

        process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        try:
            memory_data = read_memory_block(process_handle, start_address, total_size, step, mode)
        except Exception as e:
            self.tree.insert("", "end", values=(f"Error: {e}", "", "", ""))
            ctypes.windll.kernel32.CloseHandle(process_handle)
            return
        ctypes.windll.kernel32.CloseHandle(process_handle)

        # Insert the memory data into the Treeview and check for changes.
        for offset, abs_addr, value, hex_value in memory_data:
            tag = ""
            # Compare with previous value for this offset.
            prev_val = self.previous_values.get(offset)
            if prev_val is not None and prev_val != value:
                tag = "changed"
            self.tree.insert("", "end", values=(hex(offset), hex(abs_addr), value, hex_value), tags=(tag,))
            # Save the new value.
            self.previous_values[offset] = value

    def copy_selected(self):
        """Copy the selected rows' values to the clipboard."""
        selected = self.tree.selection()
        if not selected:
            return
        lines = []
        for item in selected:
            vals = self.tree.item(item, "values")
            # Join the values with tabs.
            lines.append("\t".join(str(v) for v in vals))
        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Selected values copied to clipboard.")

    def auto_refresh(self):
        """Auto-refresh the memory scan every 500 ms."""
        self.scan_memory()
        self.after(500, self.auto_refresh)


# --- Main ---

if __name__ == "__main__":
    app = DynamicPointerWindow()
    app.mainloop()
