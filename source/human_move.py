import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import math
import pybullet as p
import pybullet_data
import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.optimize import minimize
import time
import pandas as pd
import ahrs
from ahrs.filters import Madgwick

# --- 0. 数据加载和预处理 ---
def load_and_preprocess_data(filepath, sensor_link_names):
    """
    加载CSV数据并将其从原始传感器读数转换为四元数。
    """
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"错误：找不到文件 {filepath}")
        return None

    sensor_columns = {
        'thigh_r': ['accelerometer_right_thigh_x', 'accelerometer_right_thigh_y', 'accelerometer_right_thigh_z', 'gyroscope_right_thigh_x', 'gyroscope_right_thigh_y', 'gyroscope_right_thigh_z'],
        'shank_r': ['accelerometer_right_shin_x', 'accelerometer_right_shin_y', 'accelerometer_right_shin_z', 'gyroscope_right_shin_x', 'gyroscope_right_shin_y', 'gyroscope_right_shin_z'],
        'foot_r':  ['accelerometer_right_foot_x', 'accelerometer_right_foot_y', 'accelerometer_right_foot_z', 'gyroscope_right_foot_x', 'gyroscope_right_foot_y', 'gyroscope_right_foot_z'],
        'thigh_l': ['accelerometer_left_thigh_x', 'accelerometer_left_thigh_y', 'accelerometer_left_thigh_z', 'gyroscope_left_thigh_x', 'gyroscope_left_thigh_y', 'gyroscope_left_thigh_z'],
        'shank_l': ['accelerometer_left_shin_x', 'accelerometer_left_shin_y', 'accelerometer_left_shin_z', 'gyroscope_left_shin_x', 'gyroscope_left_shin_y', 'gyroscope_left_shin_z'],
        'foot_l':  ['accelerometer_left_foot_x', 'accelerometer_left_foot_y', 'accelerometer_left_foot_z', 'gyroscope_left_foot_x', 'gyroscope_left_foot_y', 'gyroscope_left_foot_z'],
    }

    # 假设采样率为100Hz
    filters = {name: Madgwick(frequency=100.0) for name in sensor_link_names}
    # 为每个连杆存储其最新的四元数，初始为单位四元数 [w, x, y, z]
    last_quats = {name: np.array([1.0, 0.0, 0.0, 0.0]) for name in sensor_link_names}
    
    all_frames_quats = []

    for index, row in df.iterrows():
        frame_quats = {}
        for link_name in sensor_link_names:
            columns = sensor_columns[link_name]
            
            # 归一化加速度数据
            accel = row[columns[0:3]].values.astype(float) / 16384.0
            gyro = np.radians(row[columns[3:6]].values.astype(float))
            
            # 获取该连杆上一时刻的四元数
            q_prev = last_quats[link_name]

            # 使用正确的参数和顺序调用 updateIMU
            q_new = filters[link_name].updateIMU(q_prev, gyro, accel)
            
            # 更新字典，为下一次迭代做准备
            last_quats[link_name] = q_new
            
            # PyBullet 使用 (x, y, z, w) 格式，所以需要调整顺序
            frame_quats[link_name] = np.array([q_new[1], q_new[2], q_new[3], q_new[0]])

        ordered_quats = [frame_quats[name] for name in sensor_link_names]
        all_frames_quats.append(ordered_quats)

    print(f"数据加载完成，共处理 {len(all_frames_quats)} 帧。")
    return all_frames_quats

# --- 1. 初始化 PyBullet ---
physicsClient = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)
planeId = p.loadURDF("plane.urdf")
robotId = p.loadURDF("humanoid_generated.urdf", [0, 0, 0.8], useFixedBase=True)

# --- 2. 获取关节和连杆的索引 ---
joint_names = [
    "hip_r", "knee_r", "ankle_r",
    "hip_l", "knee_l", "ankle_l"
]
link_names = [
    "thigh_r", "shank_r", "foot_r",
    "thigh_l", "shank_l", "foot_l"
]

joint_indices = {name: -1 for name in joint_names}
link_indices = {name: -1 for name in link_names}
joint_bounds = {}

for i in range(p.getNumJoints(robotId)):
    joint_info = p.getJointInfo(robotId, i)
    j_name = joint_info[1].decode('UTF-8')
    l_name = joint_info[12].decode('UTF-8')
    
    if j_name in joint_names:
        joint_indices[j_name] = i
        joint_bounds[j_name] = (joint_info[8], joint_info[9])

    if l_name in link_names:
        link_indices[l_name] = i

ordered_joint_indices = [joint_indices[name] for name in joint_names]
ordered_link_indices = [link_indices[name] for name in link_names]
bounds = [joint_bounds[name] for name in joint_names]

print(f"待优化的关节索引: {ordered_joint_indices}")
print(f"带传感器的连杆索引: {ordered_link_indices}")
print(f"关节边界: {bounds}")

target_quats_ordered = []

# --- 3. 定义误差函数 ---
def cost_function(angles):
    """
    计算当前关节角度下，模型姿态与传感器目标姿态的误差
    """
    for i, joint_index in enumerate(ordered_joint_indices):
        p.resetJointState(robotId, joint_index, angles[i])

    total_error = 0
    
    current_states = p.getLinkStates(robotId, ordered_link_indices)
    for i, state in enumerate(current_states):
        model_quat = state[1] 
        target_quat = target_quats_ordered[i]

        q_model_inv = list(model_quat)
        q_model_inv[3] = -q_model_inv[3]
        
        diff_w = target_quat[3] * q_model_inv[3] - target_quat[0] * q_model_inv[0] - target_quat[1] * q_model_inv[1] - target_quat[2] * q_model_inv[2]
        
        error = (1.0 - diff_w**2)
        total_error += error

    return total_error

# --- 4. 主循环：实现实时识别 ---
csv_file_path = './data/HuGaDB_v2_various_01_13.csv'
all_frames_quats = load_and_preprocess_data(csv_file_path, link_names)

if all_frames_quats is not None:
    initial_guess = np.array([0.0] * len(joint_names)) 
    frame_index = 0

    while True:
        if frame_index >= len(all_frames_quats):
            print("数据播放完毕，重置...")
            frame_index = 0 

        target_quats_ordered = all_frames_quats[frame_index]
        
        result = minimize(
            fun=cost_function,
            x0=initial_guess,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 50, 'ftol': 1e-6} 
        )
        
        final_angles = result.x
        
        initial_guess = final_angles

        for i, joint_index in enumerate(ordered_joint_indices):
            p.resetJointState(robotId, joint_index, final_angles[i])

        p.stepSimulation()
        # --- ✅ 核心改动: 增加延时以减慢动画速度 ---
        # 原来的 1./240. 速度非常快。
        # 改为 1./30. 大约是每秒30帧，您可以根据需要调整这个值。
        # 更大的分母意味着更快的速度，更小的分母意味着更慢的速度。
        time.sleep(1./30.)
        frame_index += 1
else:
    print("数据加载失败，程序退出。")

p.disconnect()
