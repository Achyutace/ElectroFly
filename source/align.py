import numpy as np
from scipy.spatial.transform import Rotation

# 辅助函数：处理四元数格式 (scipy 使用 [x, y, z, w] 格式)
def to_scipy_quat(quat):
    """将 [w, x, y, z] 格式的四元数转换为 scipy 的 [x, y, z, w] 格式"""
    return quat[..., [1, 2, 3, 0]]

def to_wxyz_quat(quat):
    """将 scipy 的 [x, y, z, w] 格式的四元数转换为 [w, x, y, z] 格式"""
    return quat[..., [3, 0, 1, 2]]

def find_rotation_axis(proximal_q: np.ndarray, distal_q: np.ndarray, fs: float) -> np.ndarray:
    """
    通过分析两个节段之间的相对运动，使用SVD/协方差找到主旋转轴。
    这个轴在近端和远端传感器的坐标系中都有定义。

    参数:
    - proximal_q (np.ndarray): 近端传感器的四元数数据 (N, 4)，格式为 [w, x, y, z]
    - distal_q (np.ndarray): 远端传感器的四元数数据 (N, 4)，格式为 [w, x, y, z]
    - fs (float): 采样频率 (Hz)

    返回:
    - axis_p (np.ndarray): 在近端传感器坐标系下的旋转轴 (3,)
    - axis_d (np.ndarray): 在远端传感器坐标系下的旋转轴 (3,)
    """
    # 1. 转换为Scipy的Rotation对象
    prox_rot = Rotation.from_quat(to_scipy_quat(proximal_q))
    dist_rot = Rotation.from_quat(to_scipy_quat(distal_q))

    # 2. 计算远端相对于近端传感器的相对旋转
    # q_relative = q_distal * q_proximal_inverse
    relative_rotation = dist_rot * prox_rot.inv()

    # 3. 计算该相对旋转的角速度。
    # 这个角速度向量是在“近端传感器”的坐标系中表示的。
    # 我们使用切片[1:]和[:-1]来计算时间差分，这比np.roll更安全，可以避免在数据末尾产生一个虚假的巨大角速度。
    delta_relative_rotation = relative_rotation[:-1].inv() * relative_rotation[1:]
    relative_ang_vel = delta_relative_rotation.as_rotvec() * fs
    
    if relative_ang_vel.shape[0] < 2:
        raise ValueError("数据点太少，无法计算角速度。")

    # 4. 使用协方差矩阵的特征向量来稳健地找到主旋转轴。
    # 这个轴（axis_p）是在近端传感器的坐标系下表示的。
    covariance_matrix = np.cov(relative_ang_vel.T)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)
    axis_p = eigenvectors[:, -1]  # 最大特征值对应的特征向量

    # 5. 为了在远端传感器的坐标系中表示这个轴，我们需要用平均相对旋转来变换它。
    # v_d = q_rel * v_p * q_rel_inv
    mean_relative_rotation = (dist_rot * prox_rot.inv()).mean()
    axis_d = mean_relative_rotation.apply(axis_p)

    # 返回归一化的轴向量
    return axis_p / np.linalg.norm(axis_p), axis_d / np.linalg.norm(axis_d)


def create_anatomical_frame(primary_axis: np.ndarray, longitudinal_axis: np.ndarray) -> Rotation:
    """
    根据主轴（ML轴）和纵轴（SI轴）构建解剖坐标系。
    假设: X = ML, Y = SI, Z = AP (Anterior-Posterior)
    使用格拉姆-施密特正交化过程。

    参数:
    - primary_axis (np.ndarray): 功能性动作确定的内外侧轴 (ML)
    - longitudinal_axis (np.ndarray): 静态校准确定的身体节段纵轴 (SI)

    返回:
    - Rotation: 从传感器坐标系到解剖坐标系的旋转对象
    """
    # 1. 定义内外侧轴 (X轴)
    x_axis = primary_axis / np.linalg.norm(primary_axis)

    # 2. 通过叉乘创建前后轴 (Z轴)，确保其与X轴正交
    # Z = X x Y_temp
    z_axis_temp = np.cross(x_axis, longitudinal_axis)
    z_axis = z_axis_temp / np.linalg.norm(z_axis_temp)

    # 3. 再次叉乘创建真正的上下轴 (Y轴)，确保三轴正交
    # Y = Z x X
    y_axis = np.cross(z_axis, x_axis)
    y_axis = y_axis / np.linalg.norm(y_axis)
    
    # 构建从传感器坐标系到解剖坐标系的旋转矩阵
    # 矩阵的列是解剖轴在传感器坐标系下的表示
    rotation_matrix = np.array([x_axis, y_axis, z_axis]).T
    
    return Rotation.from_matrix(rotation_matrix)


def perform_calibration(static_data: dict, hip_data: dict, knee_data: dict, ankle_data: dict, fs: float) -> dict:
    """
    执行完整的静态和功能性校准流程。

    参数:
    - static_data (dict): key为传感器位置 ('left_thigh', 'right_shank', etc.), 
                          value为静态站立时的四元数数据 (N, 4) in [w, x, y, z]
    - hip_data (dict): 用于髋关节校准的数据
    - knee_data (dict): 用于膝关节校准的数据
    - ankle_data (dict): 用于踝关节校准的数据
    - fs (float): 采样频率

    返回:
    - calibration_quats (dict): key为传感器位置, value为校准四元数 [w, x, y, z]
    """
    calibration_quats = {}
    sides = ['left', 'right']
    
    # 假设全局坐标系的Y轴是向上的（反重力方向）
    global_up_vector = np.array([0, 1, 0])

    for side in sides:
        # --- 1. 获取所有相关传感器的数据 ---
        thigh_q_static = static_data[f'{side}_thigh']
        shank_q_static = static_data[f'{side}_shank']
        foot_q_static = static_data[f'{side}_foot']
        
        # --- 2. 静态校准：确定各节段的纵轴方向 ---
        # 计算静态时的平均姿态
        thigh_rot_static_mean = Rotation.from_quat(to_scipy_quat(thigh_q_static)).mean()
        shank_rot_static_mean = Rotation.from_quat(to_scipy_quat(shank_q_static)).mean()
        foot_rot_static_mean = Rotation.from_quat(to_scipy_quat(foot_q_static)).mean()

        # 将全局"up"向量转换到各个传感器的坐标系中，作为纵轴的近似
        thigh_long_axis = thigh_rot_static_mean.inv().apply(global_up_vector)
        shank_long_axis = shank_rot_static_mean.inv().apply(global_up_vector)
        # 对于脚，纵轴通常指向前方，这里我们依然用静态时的Y轴做近似，可以根据具体模型调整
        foot_long_axis = foot_rot_static_mean.inv().apply(global_up_vector)

        # --- 3. 功能性校准：确定各关节的运动轴 (ML轴) ---
        
        # 膝关节 -> 确定大腿和小腿的ML轴
        # 假设骨盆固定，大腿传感器可用于近似骨盆
        knee_thigh_q = knee_data[f'{side}_thigh']
        knee_shank_q = knee_data[f'{side}_shank']
        knee_axis_thigh, knee_axis_shank = find_rotation_axis(knee_thigh_q, knee_shank_q, fs)
        
        # 髋关节 -> 确定大腿的ML轴 (可以用来验证或替代膝关节的结果)
        # 假设深蹲时身体相对于全局坐标系运动
        hip_thigh_q = hip_data[f'{side}_thigh']
        # 假设骨盆是固定的，所以proximal_q是单位四元数
        hip_axis_thigh, _ = find_rotation_axis(np.tile([1,0,0,0], (len(hip_thigh_q),1)), hip_thigh_q, fs)
        
        # 踝关节 -> 确定小腿和脚的ML轴
        ankle_shank_q = ankle_data[f'{side}_shank']
        ankle_foot_q = ankle_data[f'{side}_foot']
        ankle_axis_shank, ankle_axis_foot = find_rotation_axis(ankle_shank_q, ankle_foot_q, fs)
        
        # --- 4. 构建解剖坐标系并计算校准四元数 ---
        
        # 大腿: 使用膝关节动作确定的轴更可靠，因为它隔离了膝关节
        # 我们可以通过点乘检查髋关节和膝关节找到的轴是否一致
        print(f"[{side.upper()} Thigh] Dot product of ML axes (Knee vs Hip): {np.dot(knee_axis_thigh, hip_axis_thigh):.3f}")
        thigh_ml_axis = knee_axis_thigh
        thigh_cal_rot = create_anatomical_frame(thigh_ml_axis, thigh_long_axis)
        
        # 小腿: 同样使用膝关节动作确定的轴
        shank_ml_axis = knee_axis_shank
        shank_cal_rot = create_anatomical_frame(shank_ml_axis, shank_long_axis)
        
        # 脚: 使用踝关节动作确定的轴
        foot_ml_axis = ankle_axis_foot
        foot_cal_rot = create_anatomical_frame(foot_ml_axis, foot_long_axis)

        # --- 5. 存储校准四元数 ---
        # 这个四元数代表了从传感器坐标系到解剖坐标系的旋转
        calibration_quats[f'{side}_thigh'] = to_wxyz_quat(thigh_cal_rot.as_quat())
        calibration_quats[f'{side}_shank'] = to_wxyz_quat(shank_cal_rot.as_quat())
        calibration_quats[f'{side}_foot'] = to_wxyz_quat(foot_cal_rot.as_quat())

    return calibration_quats

# --- 这是一个示例，你需要用你自己的真实数据替换它 ---
if __name__ == '__main__':
    # 采样频率
    FS = 100.0  # Hz

    # 生成一些模拟数据 (在真实场景中，你需要从文件中加载这些数据)
    # 创建一个围绕X轴旋转的四元数序列
    t = np.arange(0, 5, 1/FS)
    angle = np.pi/2 * (1 - np.cos(0.5 * np.pi * t)) # 模拟一个平滑的屈曲动作
    # 模拟膝关节屈伸
    sim_knee_rot = Rotation.from_rotvec(np.c_[angle, np.zeros_like(angle), np.zeros_like(angle)])
    # 模拟一个初始的、随机的传感器放置偏移
    thigh_offset = Rotation.from_euler('xyz', [10, -5, 20], degrees=True)
    shank_offset = Rotation.from_euler('xyz', [-8, 15, -10], degrees=True)

    # 膝关节校准数据
    q_thigh_knee = to_wxyz_quat((thigh_offset).as_quat())[np.newaxis, :]
    q_thigh_knee = np.tile(q_thigh_knee, (len(t), 1))
    q_shank_knee = to_wxyz_quat((sim_knee_rot * shank_offset).as_quat())
    
    # 静态校准数据 (假设传感器只是带有偏移，没有运动)
    q_thigh_static = np.tile(to_wxyz_quat(thigh_offset.as_quat()), (100, 1))
    q_shank_static = np.tile(to_wxyz_quat(shank_offset.as_quat()), (100, 1))
    q_foot_static = np.tile(to_wxyz_quat(Rotation.from_euler('xyz', [5,5,5], degrees=True).as_quat()), (100, 1))

    # 将数据整理成字典格式
    # 注意：这是一个简化的例子，只演示左腿
    static_data_sim = {
        'left_thigh': q_thigh_static,
        'left_shank': q_shank_static,
        'left_foot': q_foot_static,
        # 你需要为右腿也提供数据
        'right_thigh': q_thigh_static,
        'right_shank': q_shank_static,
        'right_foot': q_foot_static,
    }
    
    knee_data_sim = {
        'left_thigh': q_thigh_knee,
        'left_shank': q_shank_knee,
        'right_thigh': q_thigh_knee,
        'right_shank': q_shank_knee,
    }
    
    # 髋关节和踝关节数据也需要用类似的方式准备
    # 为简化，这里我们复用数据
    hip_data_sim = knee_data_sim
    ankle_data_sim = {
        'left_shank': q_thigh_knee,  # 模拟近端
        'left_foot': q_shank_knee,   # 模拟远端
        'right_shank': q_thigh_knee,
        'right_foot': q_shank_knee,
    }

    # --- 2. 执行校准 ---
    calibration_results = perform_calibration(
        static_data=static_data_sim,
        hip_data=hip_data_sim,
        knee_data=knee_data_sim,
        ankle_data=ankle_data_sim,
        fs=FS
    )

    # --- 3. 查看结果 ---
    print("\n--- Calibration Results (q_cal) ---")
    for sensor, quat in calibration_results.items():
        print(f"{sensor}: [w, x, y, z] = [{quat[0]:.4f}, {quat[1]:.4f}, {quat[2]:.4f}, {quat[3]:.4f}]")

    # --- 4. 应用校准 ---
    print("\n--- How to Apply Calibration ---")
    
    # 获取一个原始的传感器四元数数据点
    raw_q_shank = q_shank_knee[50] # [w, x, y, z]
    
    # 获取对应的校准四元数
    q_cal_shank = calibration_results['left_shank']

    # 使用scipy进行计算
    raw_rot = Rotation.from_quat(to_scipy_quat(raw_q_shank))
    cal_rot = Rotation.from_quat(to_scipy_quat(q_cal_shank))

    # 这是关键的转换公式
    # q_anatomical = q_raw * q_cal_inv
    anatomical_rot = raw_rot * cal_rot.inv()
    
    q_anatomical = to_wxyz_quat(anatomical_rot.as_quat())
    anatomical_euler_angles = anatomical_rot.as_euler('xyz', degrees=True)

    print(f"Raw Shank Quaternion: [w,x,y,z] = [{raw_q_shank[0]:.3f}, {raw_q_shank[1]:.3f}, {raw_q_shank[2]:.3f}, {raw_q_shank[3]:.3f}]")
    print(f"Calibration Quaternion: [w,x,y,z] = [{q_cal_shank[0]:.3f}, {q_cal_shank[1]:.3f}, {q_cal_shank[2]:.3f}, {q_cal_shank[3]:.3f}]")
    print(f"Anatomical (Calibrated) Shank Quaternion: [w,x,y,z] = [{q_anatomical[0]:.3f}, {q_anatomical[1]:.3f}, {q_anatomical[2]:.3f}, {q_anatomical[3]:.3f}]")
    print(f"Anatomical Euler Angles (deg, XYZ): [Flex/Ext, Ab/Ad, Int/Ext] = {np.array2string(anatomical_euler_angles, formatter={'float_kind':lambda x: '%.2f' % x})}")