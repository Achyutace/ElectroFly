import serial
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import datetime

# ✅ Configure serial port
PORT = "/dev/tty.usbmodemF412FA9C80B82"  # <- Change if needed
BAUD = 115200
ser = serial.Serial(PORT, BAUD)
print(f"✅ Connected to serial port {PORT}, waiting for data...")

# ✅ State control
reading = False
calibrating = True
headers = []
data_rows = []

# ✅ Sampling rate tracking
sample_count = 0
last_time = time.time()

# ✅ Plot window settings
window_size = 200
x_data, pitch_data, roll_data, yaw_data = [], [], [], []

fig, ax = plt.subplots()
line_pitch, = ax.plot([], [], label='Pitch')
line_roll, = ax.plot([], [], label='Roll')
line_yaw, = ax.plot([], [], label='Yaw')
status_text = ax.text(0.02, 0.95, "Waiting for calibration...", transform=ax.transAxes,
                      fontsize=12, color="red", verticalalignment="top")

ax.set_title("IMU Real-Time Orientation (Euler Angles)")
ax.set_xlabel("Sample Count")
ax.set_ylabel("Angle (°)")
ax.set_ylim(-180, 180)
ax.set_xlim(0, window_size)
ax.legend()
ax.grid(True)

# ✅ Animation update function
def update(frame):
    global reading, calibrating, headers, sample_count, last_time

    while ser.in_waiting:
        try:
            raw = ser.readline()
            line = raw.decode('utf-8', errors='ignore').strip()
        except Exception as e:
            print(f"Decode error: {e}")
            continue

        # Calibration status update
        if line.startswith("Calibrating"):
            calibrating = True
            status_text.set_text("🟡 Calibrating...")
            continue

        if line == "===CALIBRATION_DONE===":
            print("🛠 Calibration done, waiting for data start...")
            calibrating = False
            status_text.set_text("🟡 Waiting to start data stream...")
            continue

        if line == "===START===":
            reading = True
            status_text.set_text("✅ Receiving data")
            print("🚀 Start receiving data")
            continue

        if not reading:
            continue

        if line.startswith("timestamp"):
            headers.clear()
            headers.extend(line.split("\t"))
            print("📋 Headers recognized:", headers)
            continue

        values = line.split("\t")
        if len(values) != len(headers):
            continue  # Skip malformed lines

        row = dict(zip(headers, values))
        data_rows.append(row)
        sample_count += 1

        try:
            x_data.append(len(x_data))
            pitch_data.append(float(row["pitch"]))
            roll_data.append(float(row["roll"]))
            yaw_data.append(float(row["yaw"]))

            if len(x_data) > window_size:
                x_data.pop(0)
                pitch_data.pop(0)
                roll_data.pop(0)
                yaw_data.pop(0)

        except ValueError:
            continue

    # Sampling rate output
    now = time.time()
    if now - last_time >= 1.0:
        print(f"📈 Current sampling rate: {sample_count} Hz")
        sample_count = 0
        last_time = now

    # Update plot safely
    if len(pitch_data) > 1:
        line_pitch.set_data(range(len(pitch_data)), pitch_data)
        line_roll.set_data(range(len(roll_data)), roll_data)
        line_yaw.set_data(range(len(yaw_data)), yaw_data)
        ax.set_xlim(max(0, len(pitch_data) - window_size), len(pitch_data))

    return line_pitch, line_roll, line_yaw, status_text

# ✅ Start real-time animation (avoid unbounded cache)
ani = FuncAnimation(fig, update, interval=100, cache_frame_data=False)
plt.show()

# ✅ Close serial and save data
ser.close()
print("🔒 Serial port closed")

if data_rows and headers:
    df = pd.DataFrame(data_rows, columns=headers)
    numeric_cols = ["timestamp", "value_x", "value_y", "value_z", "roll", "pitch", "yaw", "raw_signal"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"imu_data_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Data saved to {filename}")
else:
    print("⚠️ No valid data collected")
