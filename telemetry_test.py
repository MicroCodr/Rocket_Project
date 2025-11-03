"""
Enhanced Rocket Telemetry Visualization
Supports: Serial, TCP Sockets, gRPC, and Simulation modes
Features: Multi-graph display, configurable axes, connection management
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import math
import random
import json
from datetime import datetime
from collections import deque

# Optional imports - will gracefully handle if not installed
try:
    import serial
    import serial.tools.list_ports

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not installed. Serial mode unavailable.")

try:
    import socket

    SOCKET_AVAILABLE = True
except ImportError:
    SOCKET_AVAILABLE = False


class DataSource:
    """Base class for data sources"""

    def __init__(self):
        self.connected = False

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def read_data(self):
        raise NotImplementedError


class SimulatorSource(DataSource):
    """Simulated rocket data"""

    def __init__(self):
        super().__init__()
        self.time = 0

    def connect(self):
        self.connected = True
        self.time = 0
        return True, "Simulator started"

    def disconnect(self):
        self.connected = False

    def read_data(self):
        if not self.connected:
            return None

        self.time += 0.1

        # Flight phases
        if self.time < 2:
            phase = "Pre-Launch"
            altitude = 0
            velocity = 0
            acceleration = 0
        elif self.time < 15:
            phase = "Powered Ascent"
            altitude = 0.5 * 9.8 * (self.time - 2) ** 2
            velocity = 9.8 * (self.time - 2)
            acceleration = 9.8 + random.uniform(-0.5, 0.5)
        elif self.time < 25:
            phase = "Coasting"
            max_vel = 9.8 * 13
            altitude = (0.5 * 9.8 * 13 ** 2) + max_vel * (self.time - 15) - 0.5 * 3 * (self.time - 15) ** 2
            velocity = max_vel - 3 * (self.time - 15)
            acceleration = -3 + random.uniform(-0.2, 0.2)
        elif self.time < 27:
            phase = "Apogee"
            altitude = (0.5 * 9.8 * 13 ** 2) + 9.8 * 13 * 10 - 0.5 * 3 * 10 ** 2
            velocity = 0
            acceleration = 0
        elif self.time < 50:
            phase = "Descent"
            apogee = (0.5 * 9.8 * 13 ** 2) + 9.8 * 13 * 10 - 0.5 * 3 * 10 ** 2
            altitude = apogee - 5 * (self.time - 27)
            velocity = -5
            acceleration = -1 + random.uniform(-0.1, 0.1)
        else:
            phase = "Landed"
            altitude = 0
            velocity = 0
            acceleration = 0

        altitude = max(0, altitude + random.uniform(-2, 2))

        return {
            'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
            'flight_time': round(self.time, 2),
            'phase': phase,
            'altitude': round(altitude, 2),
            'velocity': round(velocity, 2),
            'acceleration': round(acceleration, 2),
            'temperature': round(20 - altitude * 0.0065 + random.uniform(-1, 1), 2),
            'pressure': round(101.325 * math.exp(-altitude / 8500) + random.uniform(-0.1, 0.1), 2),
        }


class SerialSource(DataSource):
    """Serial port data source"""

    def __init__(self, port, baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial = None

    def connect(self):
        if not SERIAL_AVAILABLE:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for connection
            self.connected = True
            return True, f"Connected to {self.port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial:
            self.serial.close()
        self.connected = False

    def read_data(self):
        if not self.connected or not self.serial:
            return None
        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8').strip()
                # Expecting JSON format: {"altitude": 100, "velocity": 50, ...}
                return json.loads(line)
        except Exception as e:
            print(f"Serial read error: {e}")
        return None


class TCPSocketSource(DataSource):
    """TCP Socket data source"""

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        if not SOCKET_AVAILABLE:
            return False, "Socket support not available"
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True, f"Connected to {self.host}:{self.port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.socket:
            self.socket.close()
        self.connected = False

    def read_data(self):
        if not self.connected or not self.socket:
            return None
        try:
            self.socket.settimeout(0.1)
            data = self.socket.recv(1024).decode('utf-8').strip()
            if data:
                # Expecting JSON format
                return json.loads(data)
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Socket read error: {e}")
        return None


class TelemetryGUI:
    """Enhanced GUI with multiple graphs and connection options"""

    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Rocket Telemetry Monitor")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0e27')

        # Data management
        self.data_queue = queue.Queue()
        self.data_history = {
            'time': deque(maxlen=500),
            'altitude': deque(maxlen=500),
            'velocity': deque(maxlen=500),
            'acceleration': deque(maxlen=500),
            'temperature': deque(maxlen=500),
            'pressure': deque(maxlen=500),
        }

        # Connection management
        self.data_source = None
        self.running = False
        self.reader_thread = None

        # Create UI
        self.create_widgets()
        self.update_gui()

    def create_widgets(self):
        """Create all UI elements"""

        # Top bar - Connection controls
        top_frame = tk.Frame(self.root, bg='#1a1f3a', height=100)
        top_frame.pack(fill='x', padx=5, pady=5)
        top_frame.pack_propagate(False)

        # Title
        title = tk.Label(top_frame, text="🚀 ENHANCED TELEMETRY SYSTEM",
                         font=('Arial', 18, 'bold'), bg='#1a1f3a', fg='#00ff88')
        title.grid(row=0, column=0, columnspan=4, pady=10, padx=10, sticky='w')

        # Connection type selector
        tk.Label(top_frame, text="Source:", font=('Arial', 10),
                 bg='#1a1f3a', fg='#ffffff').grid(row=1, column=0, padx=5, sticky='e')

        self.source_var = tk.StringVar(value="Simulator")
        source_menu = ttk.Combobox(top_frame, textvariable=self.source_var,
                                   values=["Simulator", "Serial Port", "TCP Socket"],
                                   state='readonly', width=15)
        source_menu.grid(row=1, column=1, padx=5)
        source_menu.bind('<<ComboboxSelected>>', self.on_source_changed)

        # Connection parameters frame
        self.param_frame = tk.Frame(top_frame, bg='#1a1f3a')
        self.param_frame.grid(row=1, column=2, padx=10)

        # Connect button
        self.connect_btn = tk.Button(top_frame, text="Connect",
                                     command=self.toggle_connection,
                                     bg='#00aa44', fg='white', font=('Arial', 10, 'bold'),
                                     width=10, relief='raised', bd=2)
        self.connect_btn.grid(row=1, column=3, padx=10)

        # Status indicator
        self.status_label = tk.Label(top_frame, text="● DISCONNECTED",
                                     font=('Arial', 11, 'bold'),
                                     bg='#1a1f3a', fg='#ff4444')
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5, sticky='w', padx=10)

        self.phase_label = tk.Label(top_frame, text="Phase: --",
                                    font=('Arial', 11), bg='#1a1f3a', fg='#ffaa00')
        self.phase_label.grid(row=2, column=2, columnspan=2, pady=5, sticky='w')

        # Main content area
        main_frame = tk.Frame(self.root, bg='#0a0e27')
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Left side - Data cards
        left_frame = tk.Frame(main_frame, bg='#0a0e27', width=350)
        left_frame.pack(side='left', fill='both', padx=5)
        left_frame.pack_propagate(False)

        self.create_data_card(left_frame, "Altitude", "altitude_value", "m", 0)
        self.create_data_card(left_frame, "Velocity", "velocity_value", "m/s", 1)
        self.create_data_card(left_frame, "Acceleration", "accel_value", "m/s²", 2)
        self.create_data_card(left_frame, "Temperature", "temp_value", "°C", 3)
        self.create_data_card(left_frame, "Pressure", "pressure_value", "kPa", 4)
        self.create_data_card(left_frame, "Flight Time", "time_value", "s", 5)

        # Right side - Graphs
        right_frame = tk.Frame(main_frame, bg='#0a0e27')
        right_frame.pack(side='left', fill='both', expand=True, padx=5)

        # Graph 1
        self.create_graph_panel(right_frame, "graph1", 0)

        # Graph 2
        self.create_graph_panel(right_frame, "graph2", 1)

        # Bottom - Log
        log_frame = tk.Frame(self.root, bg='#1a1f3a')
        log_frame.pack(fill='x', padx=5, pady=5)

        tk.Label(log_frame, text="TELEMETRY LOG", font=('Arial', 10, 'bold'),
                 bg='#1a1f3a', fg='#00ff88').pack(anchor='w', padx=5, pady=2)

        self.log_text = tk.Text(log_frame, height=4, bg='#0a0e27', fg='#00ff88',
                                font=('Courier', 9), state='disabled')
        self.log_text.pack(fill='x', padx=5, pady=5)

        # Initialize with simulator parameters
        self.on_source_changed()

    def create_data_card(self, parent, label, attr_name, unit, row):
        """Create data display card"""
        card = tk.Frame(parent, bg='#1a1f3a', relief='solid', borderwidth=1)
        card.pack(fill='x', pady=5, padx=5)

        tk.Label(card, text=label, font=('Arial', 10),
                 bg='#1a1f3a', fg='#888888').pack(pady=(8, 2))

        value_label = tk.Label(card, text="--", font=('Arial', 28, 'bold'),
                               bg='#1a1f3a', fg='#00ff88')
        value_label.pack()

        tk.Label(card, text=unit, font=('Arial', 9),
                 bg='#1a1f3a', fg='#666666').pack(pady=(0, 8))

        setattr(self, attr_name, value_label)

    def create_graph_panel(self, parent, graph_name, row):
        """Create graph panel with controls"""
        frame = tk.Frame(parent, bg='#1a1f3a', relief='solid', borderwidth=1)
        frame.pack(fill='both', expand=True, pady=5)

        # Controls
        control_frame = tk.Frame(frame, bg='#1a1f3a')
        control_frame.pack(fill='x', padx=5, pady=5)

        tk.Label(control_frame, text="Y-Axis:", font=('Arial', 9),
                 bg='#1a1f3a', fg='#ffffff').pack(side='left', padx=5)

        y_var = tk.StringVar(value="altitude" if graph_name == "graph1" else "velocity")
        y_menu = ttk.Combobox(control_frame, textvariable=y_var,
                              values=["altitude", "velocity", "acceleration", "temperature", "pressure"],
                              state='readonly', width=12, font=('Arial', 9))
        y_menu.pack(side='left', padx=5)

        setattr(self, f"{graph_name}_y_var", y_var)
        setattr(self, f"{graph_name}_y_menu", y_menu)

        # Canvas
        canvas = tk.Canvas(frame, bg='#0a0e27', highlightthickness=0, height=180)
        canvas.pack(fill='both', expand=True, padx=5, pady=5)

        setattr(self, f"{graph_name}_canvas", canvas)

    def on_source_changed(self, event=None):
        """Update parameter inputs based on source type"""
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        source = self.source_var.get()

        if source == "Serial Port":
            tk.Label(self.param_frame, text="Port:", bg='#1a1f3a', fg='#ffffff').grid(row=0, column=0, padx=2)
            self.port_var = tk.StringVar(value="/dev/cu.usbserial-0001")

            if SERIAL_AVAILABLE:
                ports = [p.device for p in serial.tools.list_ports.comports()]
                port_menu = ttk.Combobox(self.param_frame, textvariable=self.port_var,
                                         values=ports if ports else ["/dev/cu.usbserial-0001"],
                                         width=20)
            else:
                port_menu = tk.Entry(self.param_frame, textvariable=self.port_var, width=22)
            port_menu.grid(row=0, column=1, padx=2)

            tk.Label(self.param_frame, text="Baud:", bg='#1a1f3a', fg='#ffffff').grid(row=0, column=2, padx=2)
            self.baud_var = tk.StringVar(value="9600")
            baud_menu = ttk.Combobox(self.param_frame, textvariable=self.baud_var,
                                     values=["9600", "115200", "57600", "38400"],
                                     width=8, state='readonly')
            baud_menu.grid(row=0, column=3, padx=2)

        elif source == "TCP Socket":
            tk.Label(self.param_frame, text="Host:", bg='#1a1f3a', fg='#ffffff').grid(row=0, column=0, padx=2)
            self.host_var = tk.StringVar(value="192.168.1.100")
            tk.Entry(self.param_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=2)

            tk.Label(self.param_frame, text="Port:", bg='#1a1f3a', fg='#ffffff').grid(row=0, column=2, padx=2)
            self.socket_port_var = tk.StringVar(value="5000")
            tk.Entry(self.param_frame, textvariable=self.socket_port_var, width=8).grid(row=0, column=3, padx=2)

    def toggle_connection(self):
        """Connect or disconnect from data source"""
        if not self.running:
            # Connect
            source_type = self.source_var.get()

            if source_type == "Simulator":
                self.data_source = SimulatorSource()
            elif source_type == "Serial Port":
                port = self.port_var.get()
                baud = int(self.baud_var.get())
                self.data_source = SerialSource(port, baud)
            elif source_type == "TCP Socket":
                host = self.host_var.get()
                port = int(self.socket_port_var.get())
                self.data_source = TCPSocketSource(host, port)
            else:
                messagebox.showerror("Error", "Unknown source type")
                return

            success, message = self.data_source.connect()

            if success:
                self.running = True
                self.reader_thread = threading.Thread(target=self.read_data_thread, daemon=True)
                self.reader_thread.start()

                self.connect_btn.config(text="Disconnect", bg='#aa0000')
                self.status_label.config(text="● CONNECTED", fg='#00ff00')
                self.log_message(f"Connected: {message}")
            else:
                messagebox.showerror("Connection Error", message)
        else:
            # Disconnect
            self.running = False
            if self.data_source:
                self.data_source.disconnect()

            self.connect_btn.config(text="Connect", bg='#00aa44')
            self.status_label.config(text="● DISCONNECTED", fg='#ff4444')
            self.log_message("Disconnected")

    def read_data_thread(self):
        """Thread for reading data from source"""
        while self.running:
            try:
                data = self.data_source.read_data()
                if data:
                    self.data_queue.put(data)
                time.sleep(0.05)  # 20 Hz
            except Exception as e:
                print(f"Read error: {e}")
                time.sleep(0.1)

    def update_gui(self):
        """Update GUI with new data"""
        try:
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()

                # Update displays
                if 'altitude' in data:
                    self.altitude_value.config(text=f"{data['altitude']:.1f}")
                    self.data_history['altitude'].append(data['altitude'])

                if 'velocity' in data:
                    self.velocity_value.config(text=f"{data['velocity']:.1f}")
                    self.data_history['velocity'].append(data['velocity'])

                if 'acceleration' in data:
                    self.accel_value.config(text=f"{data['acceleration']:.1f}")
                    self.data_history['acceleration'].append(data['acceleration'])

                if 'temperature' in data:
                    self.temp_value.config(text=f"{data['temperature']:.1f}")
                    self.data_history['temperature'].append(data['temperature'])

                if 'pressure' in data:
                    self.pressure_value.config(text=f"{data['pressure']:.1f}")
                    self.data_history['pressure'].append(data['pressure'])

                if 'flight_time' in data:
                    self.time_value.config(text=f"{data['flight_time']:.1f}")
                    self.data_history['time'].append(data['flight_time'])

                if 'phase' in data:
                    self.phase_label.config(text=f"Phase: {data['phase']}")

                # Log
                log_msg = f"[{data.get('timestamp', datetime.now().strftime('%H:%M:%S'))}] "
                log_msg += f"ALT:{data.get('altitude', 0):.1f}m VEL:{data.get('velocity', 0):.1f}m/s "
                log_msg += data.get('phase', '--')
                self.log_message(log_msg)

                # Draw graphs
                self.draw_graph("graph1")
                self.draw_graph("graph2")

        except queue.Empty:
            pass

        self.root.after(50, self.update_gui)

    def draw_graph(self, graph_name):
        """Draw graph with selected data"""
        canvas = getattr(self, f"{graph_name}_canvas")
        y_var = getattr(self, f"{graph_name}_y_var").get()

        canvas.delete('all')

        if len(self.data_history['time']) < 2:
            return

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width < 10 or height < 10:
            return

        # Get data
        x_data = list(self.data_history['time'])
        y_data = list(self.data_history[y_var])

        if not y_data:
            return

        # Calculate scaling
        padding = 40
        graph_width = width - 2 * padding
        graph_height = height - 2 * padding

        min_y = min(y_data)
        max_y = max(y_data)
        range_y = max_y - min_y if max_y != min_y else 1

        min_x = min(x_data)
        max_x = max(x_data)
        range_x = max_x - min_x if max_x != min_x else 1

        # Draw axes
        canvas.create_line(padding, height - padding,
                           width - padding, height - padding,
                           fill='#444444', width=2)
        canvas.create_line(padding, padding,
                           padding, height - padding,
                           fill='#444444', width=2)

        # Draw grid and labels
        for i in range(5):
            y = padding + (graph_height * i / 4)
            canvas.create_line(padding, y, width - padding, y,
                               fill='#222222', dash=(2, 4))
            val = max_y - (range_y * i / 4)
            canvas.create_text(padding - 5, y, text=f"{val:.0f}",
                               anchor='e', fill='#666666', font=('Arial', 8))

        # Draw data line
        if len(x_data) > 1:
            points = []
            for i in range(len(x_data)):
                x = padding + ((x_data[i] - min_x) / range_x) * graph_width
                y = height - padding - ((y_data[i] - min_y) / range_y) * graph_height
                points.extend([x, y])

            canvas.create_line(points, fill='#00ff88', width=2, smooth=True)

        # Labels
        canvas.create_text(width / 2, height - 10,
                           text="Flight Time (s)", fill='#888888', font=('Arial', 9))

        y_labels = {
            'altitude': 'Altitude (m)',
            'velocity': 'Velocity (m/s)',
            'acceleration': 'Acceleration (m/s²)',
            'temperature': 'Temperature (°C)',
            'pressure': 'Pressure (kPa)'
        }
        canvas.create_text(15, height / 2,
                           text=y_labels.get(y_var, y_var),
                           fill='#888888', font=('Arial', 9), angle=90)

    def log_message(self, message):
        """Add message to log"""
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.see('end')

        # Keep only last 5 lines
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 5:
            self.log_text.delete('1.0', f'{lines - 4}.0')

        self.log_text.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = TelemetryGUI(root)
    root.mainloop()