import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Load previously saved data (mock template loading for now)
# In real case, replace this with actual file
template_file = Path("/mnt/data/imu_data_template.csv")

# Sample structure of the data
# Let's create a mock DataFrame for demonstration
data = {
    "timestamp": np.tile(np.arange(0, 2000, 10), 2),
    "sensor_type": ["MPU6050"] * 400,
    "location": ["left_hip"] * 200 + ["right_knee"] * 200,
    "channel": ["acc"] * 400,
    "value_x": np.random.normal(0, 1, 400),
    "value_y": np.random.normal(0, 1, 400),
    "value_z": np.random.normal(9.8, 0.2, 400),
    "roll": np.concatenate([np.linspace(0, 20, 200), np.linspace(0, -20, 200)]),
    "pitch": np.random.normal(0, 5, 400),
    "yaw": np.random.normal(0, 10, 400),
    "raw_signal": np.random.normal(0, 1, 400)
}
df = pd.DataFrame(data)

# Synchronize based on timestamp and location
pivoted = df.pivot_table(index="timestamp", columns="location", values=["roll", "pitch", "yaw"])

# Plot synchronized roll/pitch/yaw comparisons
fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
pivoted["roll"].plot(ax=axs[0], title="Roll Comparison")
pivoted["pitch"].plot(ax=axs[1], title="Pitch Comparison")
pivoted["yaw"].plot(ax=axs[2], title="Yaw Comparison")
plt.xlabel("Timestamp (ms)")
plt.tight_layout()
plt.show()

# Print first few rows
print(pivoted.head())

# Optional: Save to file
pivoted.to_csv("synced_IMU_data.csv")
print("✅ Synced data saved to synced_IMU_data.csv")

