import serial

ser = serial.Serial("/dev/tty.usbmodemF412FA9C80B82", 115200)

print("📡 Listening on serial port...")
while True:
    try:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        print("🧾", line)
    except Exception as e:
        print("⚠️ Error:", e)
        break
