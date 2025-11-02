"""
Rocket Telemetry Visualization Demo
Simulates real-time rocket telemetry data without hardware
Demonstrates: Multithreading, Data Visualization, GUI Development
"""

import tkinter as tk
from tkinter import ttk
import threading
import queue
import time
import math
import random
from datetime import datetime


class RocketTelemetrySimulator:
    """Simulates rocket flight data"""

    def __init__(self):
        self.time = 0
        self.flight_phase = "Pre-Launch"

    def get_telemetry(self):
        """Generate realistic rocket telemetry data"""
        self.time += 0.1

        # Simulate different flight phases
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
            max_velocity = 9.8 * 13
            altitude = (0.5 * 9.8 * 13 ** 2) + max_velocity * (self.time - 15) - 0.5 * 3 * (self.time - 15) ** 2
            velocity = max_velocity - 3 * (self.time - 15)
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

        # Add some noise for realism
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


class TelemetryGUI:
    """Main GUI for displaying telemetry"""

    def __init__(self, root):
        self.root = root
        self.root.title("Rocket Telemetry Monitor - Live Demo")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e1e')

        # Data queue for thread-safe communication
        self.data_queue = queue.Queue()

        # Data storage for plotting
        self.altitude_history = []
        self.velocity_history = []
        self.time_history = []
        self.max_points = 100

        # Create GUI elements
        self.create_widgets()

        # Start simulator thread
        self.running = True
        self.simulator = RocketTelemetrySimulator()
        self.sim_thread = threading.Thread(target=self.simulate_data, daemon=True)
        self.sim_thread.start()

        # Start GUI update
        self.update_gui()

    def create_widgets(self):
        """Create all GUI widgets"""

        # Header
        header = tk.Frame(self.root, bg='#2d2d2d', height=60)
        header.pack(fill='x', padx=10, pady=10)

        title = tk.Label(header, text="🚀 ROCKET TELEMETRY SYSTEM",
                         font=('Arial', 20, 'bold'), bg='#2d2d2d', fg='#00ff00')
        title.pack(pady=15)

        # Status bar
        status_frame = tk.Frame(self.root, bg='#2d2d2d')
        status_frame.pack(fill='x', padx=10, pady=5)

        self.status_label = tk.Label(status_frame, text="● CONNECTED",
                                     font=('Arial', 12, 'bold'),
                                     bg='#2d2d2d', fg='#00ff00')
        self.status_label.pack(side='left', padx=10)

        self.phase_label = tk.Label(status_frame, text="Phase: Pre-Launch",
                                    font=('Arial', 12),
                                    bg='#2d2d2d', fg='#ffaa00')
        self.phase_label.pack(side='left', padx=20)

        # Main data display
        data_frame = tk.Frame(self.root, bg='#1e1e1e')
        data_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create data cards
        self.create_data_card(data_frame, "Altitude", "altitude_value", "m", 0, 0)
        self.create_data_card(data_frame, "Velocity", "velocity_value", "m/s", 0, 1)
        self.create_data_card(data_frame, "Acceleration", "accel_value", "m/s²", 0, 2)
        self.create_data_card(data_frame, "Temperature", "temp_value", "°C", 1, 0)
        self.create_data_card(data_frame, "Pressure", "pressure_value", "kPa", 1, 1)
        self.create_data_card(data_frame, "Flight Time", "time_value", "s", 1, 2)

        # Simple graph area
        graph_frame = tk.Frame(self.root, bg='#2d2d2d', height=200)
        graph_frame.pack(fill='both', expand=True, padx=10, pady=10)
        graph_frame.pack_propagate(False)

        graph_label = tk.Label(graph_frame, text="ALTITUDE PROFILE",
                               font=('Arial', 14, 'bold'), bg='#2d2d2d', fg='#ffffff')
        graph_label.pack(pady=5)

        self.canvas = tk.Canvas(graph_frame, bg='#1a1a1a', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=10, pady=5)

        # Log area
        log_frame = tk.Frame(self.root, bg='#2d2d2d')
        log_frame.pack(fill='x', padx=10, pady=10)

        log_label = tk.Label(log_frame, text="TELEMETRY LOG",
                             font=('Arial', 10, 'bold'), bg='#2d2d2d', fg='#ffffff')
        log_label.pack(anchor='w', padx=5)

        self.log_text = tk.Text(log_frame, height=4, bg='#1a1a1a', fg='#00ff00',
                                font=('Courier', 9), state='disabled')
        self.log_text.pack(fill='x', padx=5, pady=5)

    def create_data_card(self, parent, label, attr_name, unit, row, col):
        """Create a data display card"""
        card = tk.Frame(parent, bg='#2d2d2d', relief='raised', borderwidth=2)
        card.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)

        tk.Label(card, text=label, font=('Arial', 11),
                 bg='#2d2d2d', fg='#888888').pack(pady=(10, 5))

        value_label = tk.Label(card, text="0.00", font=('Arial', 24, 'bold'),
                               bg='#2d2d2d', fg='#00ff00')
        value_label.pack()

        tk.Label(card, text=unit, font=('Arial', 10),
                 bg='#2d2d2d', fg='#888888').pack(pady=(0, 10))

        setattr(self, attr_name, value_label)

    def simulate_data(self):
        """Simulator thread - generates data"""
        while self.running:
            telemetry = self.simulator.get_telemetry()
            self.data_queue.put(telemetry)
            time.sleep(0.1)  # 10 Hz update rate

    def update_gui(self):
        """Update GUI with new data - runs in main thread"""
        try:
            # Process all available data
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()

                # Update displays
                self.altitude_value.config(text=f"{data['altitude']:.1f}")
                self.velocity_value.config(text=f"{data['velocity']:.1f}")
                self.accel_value.config(text=f"{data['acceleration']:.1f}")
                self.temp_value.config(text=f"{data['temperature']:.1f}")
                self.pressure_value.config(text=f"{data['pressure']:.1f}")
                self.time_value.config(text=f"{data['flight_time']:.1f}")

                # Update phase
                self.phase_label.config(text=f"Phase: {data['phase']}")

                # Store for graphing
                self.time_history.append(data['flight_time'])
                self.altitude_history.append(data['altitude'])
                self.velocity_history.append(data['velocity'])

                # Keep only recent data
                if len(self.time_history) > self.max_points:
                    self.time_history.pop(0)
                    self.altitude_history.pop(0)
                    self.velocity_history.pop(0)

                # Update log
                log_msg = f"[{data['timestamp']}] ALT:{data['altitude']:.1f}m VEL:{data['velocity']:.1f}m/s {data['phase']}\n"
                self.log_text.config(state='normal')
                self.log_text.insert('end', log_msg)
                self.log_text.see('end')
                # Keep only last 5 lines
                if int(self.log_text.index('end-1c').split('.')[0]) > 5:
                    self.log_text.delete('1.0', '2.0')
                self.log_text.config(state='disabled')

                # Redraw graph
                self.draw_graph()

        except queue.Empty:
            pass

        # Schedule next update
        self.root.after(50, self.update_gui)

    def draw_graph(self):
        """Draw simple altitude graph"""
        self.canvas.delete('all')

        if len(self.altitude_history) < 2:
            return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 10 or height < 10:
            return

        # Calculate scaling
        max_alt = max(self.altitude_history) if self.altitude_history else 1
        max_alt = max(max_alt, 10)  # Minimum scale

        padding = 40
        graph_width = width - 2 * padding
        graph_height = height - 2 * padding

        # Draw axes
        self.canvas.create_line(padding, height - padding,
                                width - padding, height - padding,
                                fill='#555555', width=2)
        self.canvas.create_line(padding, padding,
                                padding, height - padding,
                                fill='#555555', width=2)

        # Draw grid
        for i in range(5):
            y = padding + (graph_height * i / 4)
            self.canvas.create_line(padding, y, width - padding, y,
                                    fill='#333333', dash=(2, 4))
            alt_label = max_alt * (4 - i) / 4
            self.canvas.create_text(padding - 5, y, text=f"{alt_label:.0f}",
                                    anchor='e', fill='#888888', font=('Arial', 8))

        # Draw altitude line
        if len(self.altitude_history) > 1:
            points = []
            for i, alt in enumerate(self.altitude_history):
                x = padding + (i / (self.max_points - 1)) * graph_width
                y = height - padding - (alt / max_alt) * graph_height
                points.extend([x, y])

            self.canvas.create_line(points, fill='#00ff00', width=2, smooth=True)

        # Labels
        self.canvas.create_text(width / 2, height - 10,
                                text="Time", fill='#888888', font=('Arial', 9))
        self.canvas.create_text(15, height / 2,
                                text="Altitude (m)", fill='#888888',
                                font=('Arial', 9), angle=90)


if __name__ == "__main__":
    root = tk.Tk()
    app = TelemetryGUI(root)
    root.mainloop()