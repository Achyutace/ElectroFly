# view_urdf_with_pybullet.py

import pybullet as p
import pybullet_data
import time
import os

def view_urdf_with_pybullet(urdf_filepath):
    """
    加载并用 PyBullet 静态显示一个 URDF 文件。

    :param urdf_filepath: 要加载的URDF文件的完整路径。
    """
    # 1. 连接到 PyBullet 物理仿真服务器
    # p.GUI 会创建一个带图形界面的窗口
    # 如果已有连接，先断开，确保每次调用都是一个新环境
    if p.isConnected():
        p.disconnect()
        
    try:
        physicsClient = p.connect(p.GUI)
        print("成功连接到 PyBullet GUI。")
    except p.error as e:
        print(f"连接到 PyBullet GUI 失败: {e}")
        print("您可能没有安装图形界面相关的依赖 (例如: X11)。")
        print("尝试使用 p.DIRECT 模式进行无界面连接。")
        try:
            physicsClient = p.connect(p.DIRECT)
            print("成功连接到 PyBullet (无界面模式)。")
        except p.error as e_direct:
            print(f"无界面模式连接也失败了: {e_direct}")
            return

    # 2. 设置仿真环境
    # 添加一个数据路径，用于加载一些基础模型，比如地面
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    
    # 设置重力
    p.setGravity(0, 0, -9.8)
    
    # 加载一个地面作为参考
    planeId = p.loadURDF("plane.urdf")
    
    # 设置相机初始位置和朝向，方便观察
    p.resetDebugVisualizerCamera(
        cameraDistance=1.5,      # 相机距离目标的距离
        cameraYaw=60,            # 左右旋转角度
        cameraPitch=-30,         # 上下俯仰角度
        cameraTargetPosition=[0, 0, 0.5] # 相机对准的点
    )

    # 3. 加载 URDF 文件
    # 检查文件是否存在
    if not os.path.exists(urdf_filepath):
        print(f"错误: URDF 文件 '{urdf_filepath}' 未找到。")
        p.disconnect()
        return
        
    try:
        # 将机器人固定在基座上，使其不会因为重力掉下去
        robot_start_pos = [0, 0, 0.5]
        robot_start_orientation = p.getQuaternionFromEuler([0, 0, 0])
        robotId = p.loadURDF(urdf_filepath, robot_start_pos, robot_start_orientation, useFixedBase=True)
        print(f"成功加载模型: {urdf_filepath}")
        
        # 获取并打印关节信息
        num_joints = p.getNumJoints(robotId)
        print(f"模型包含 {num_joints} 个关节。")
        for i in range(num_joints):
            joint_info = p.getJointInfo(robotId, i)
            print(f"  - 关节 {i}: {joint_info[1].decode('utf-8')}")

    except p.error as e:
        print(f"加载 URDF 文件失败: {e}")
        p.disconnect()
        return

    # 4. 保持窗口打开
    print("\n模型已在窗口中显示。")
    print("这个窗口可以交互，用鼠标拖动来旋转/缩放/移动。")
    print("关闭可视化窗口即可结束程序。")
    
    try:
        # 创建一个循环来保持程序运行，直到窗口被关闭
        while p.isConnected():
            # 在GUI模式下，stepSimulation不是必须的，如果只是静态查看
            # 但保持一个小的延时可以降低CPU占用
            time.sleep(1./240.)
    except p.error:
        # 当用户关闭窗口时，p.isConnected()会变为False，循环自然退出
        # 或者在某些操作后（如disconnect）调用p的函数会抛出p.error
        pass
    finally:
        if p.isConnected():
            p.disconnect()
        print("PyBullet 可视化窗口已关闭。")


# --- 如何使用这个函数 ---

if __name__ == '__main__':
    # 当这个脚本被直接运行时，会执行下面的代码作为演示

    # 定义要加载的URDF文件名
    # 请确保 "humanoid_generated.urdf" 文件与此脚本在同一个目录下
    # 或者提供它的完整路径
    urdf_to_view = "humanoid_generated.urdf"

    # 直接调用函数
    view_urdf_with_pybullet(urdf_to_view)

    print("脚本执行完毕。")
