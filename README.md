 # Enhanced Rocket Telemetry Visualization System

A real-time monitoring system for tracking rocket flights with live graphs and data displays.

## What This Does

This program lets you watch rocket telemetry data in real-time on your computer. Think of it like a mission control dashboard that shows altitude, speed, and other important information as the rocket flies.

### Main Features

- **Multiple Ways to Get Data**
  - Serial Port: Connect with a USB cable
  - TCP Socket: Connect over WiFi
  - Simulator: Practice mode with fake flight data

- **Live Display**
  - Two graphs that update in real-time
  - Big number displays for quick reading
  - Shows last 500 data points (about 25 seconds)

- **Flight Tracking**
  - Altitude (how high the rocket is)
  - Velocity (how fast it's moving)
  - Acceleration (how quickly speed is changing)
  - Temperature and pressure readings
  - Automatic detection of flight phases

## Why You'd Use This

1. **Before Launch**: Test your setup with the simulator
2. **On Launch Day**: Connect to your rocket's transmitter
3. **After Flight**: Review what happened
4. **For Demos**: Show off to the club without needing a real rocket
5. **For Learning**: Understand how telemetry systems work

## How to Install

### What You Need

```bash
Python 3.7 or newer
```

### Optional: For Serial Port Support

```bash
pip install pyserial
```

### Running It

1. **Save the file**
   - Name it telemetry_test.py

2. **Install extras if needed**
   ```bash
   pip install pyserial
   ```

3. **Start the program**
   ```bash
   python telemetry_test.py
   ```

## How to Use It

### Simulator Mode (Easy Start)

This is perfect for testing and showing people how it works:

1. Open the program
2. "Simulator" should already be selected
3. Click "Connect"
4. Watch a fake rocket flight happen automatically

The simulator runs a 50-second mission from launch to landing.

### Serial Port Mode

For when you have a device plugged in with a USB cable:

1. Pick "Serial Port" from the dropdown
2. Choose your port (example: COM3 on Windows, /dev/cu.usbserial-0001 on Mac)
3. Set the speed (usually 9600)
4. Click "Connect"

**What format does it need?**
The device needs to send JSON text like this:
```json
{"altitude": 150.5, "velocity": 45.2, "acceleration": 2.1}
```

### TCP Socket Mode

For WiFi or network connections:

1. Pick "TCP Socket" from the dropdown
2. Type in the IP address (example: 192.168.1.100)
3. Type in the port number (example: 5000)
4. Click "Connect"

Uses the same JSON format as Serial mode.

## What You See on Screen

### Left Side - Big Numbers
- **Altitude**: Height in meters
- **Velocity**: Speed in m/s (positive = going up, negative = going down)
- **Acceleration**: How fast the speed is changing
- **Temperature**: Outside temperature
- **Pressure**: Air pressure (lower means higher altitude)
- **Flight Time**: Seconds since launch

### Right Side - Graphs
- Two separate graphs you can set up however you want
- Each graph can show any measurement
- X-axis always shows time
- Graphs remember the last 500 points

### Bottom - Log Window
Scrolling text showing what's happening with timestamps.

## For Club Presentations

### Quick Demo (5 minutes)

1. **Introduction** (30 seconds)
   - "Here's our ground station software for tracking rockets"

2. **Show the Simulator** (2 minutes)
   - Click Connect and let it run
   - Point out the different flight phases
   - Show how the graphs update

3. **Explain the Features** (1.5 minutes)
   - Show the connection options
   - Change what the graphs display
   - Show the scrolling log

4. **Technical Stuff** (1 minute)
   - Updates 20 times per second
   - Uses simple JSON format
   - Works with Arduino, ESP32, or other boards

5. **Questions** (30 seconds)

### Good Things to Mention

- "Works with any device that can send JSON"
- "Updates fast enough to catch everything"
- "You can test without building hardware first"
- "Easy to connect different ways"

## Technical Details

| What | Value |
|------|-------|
| Update Speed | 20 times per second |
| Data Memory | Last 500 points |
| Serial Speeds | 9600, 38400, 57600, 115200 |
| Network Type | TCP Socket |
| Data Format | JSON text |

## Connecting Your Hardware

### Arduino Example

```cpp
void loop() {
  // Read your sensors here
  float alt = readAltitude();
  float vel = readVelocity();
  
  // Send as JSON
  Serial.print("{\"altitude\":");
  Serial.print(alt);
  Serial.print(",\"velocity\":");
  Serial.print(vel);
  Serial.println("}");
  
  delay(50); // Send 20 times per second
}
```

### ESP32/ESP8266 Example (WiFi)

```cpp
WiFiClient client;
client.connect("192.168.1.5", 5000);

String json = "{\"altitude\":" + String(alt) + 
              ",\"velocity\":" + String(vel) + "}";
client.println(json);
```

## Flight Phases Explained

The program automatically figures out what the rocket is doing:

- **Pre-Launch**: Sitting on the pad
- **Powered Ascent**: Motor is firing
- **Coasting**: Motor burned out, still going up
- **Apogee**: Highest point, almost stopped
- **Descent**: Coming back down
- **Landed**: Back on the ground

## Common Problems

**"pyserial not installed" message**
- Fix: Run `pip install pyserial` in your terminal

**Can't find the serial port**
- Check the USB cable is plugged in
- Try different ports from the list
- On Mac/Linux, you might need permission to access the port

**TCP won't connect**
- Double-check the IP address
- Make sure the port number is right
- Check that both devices are on the same WiFi

**Graphs aren't moving**
- Make sure the data includes the right field names
- Check that JSON format is correct
- Verify the connection shows "CONNECTED"

## License

Free to use and modify for your rocket projects.


**Version**: 2.0  
**Last Updated**: November 2025  
**Works On**: Windows, Mac, Linux
