# view_urdf_as_function.py

import ikpy.chain
import numpy as np
import vpython as vp

def view_urdf_from_file(urdf_filepath):
    """
    加载并用VPython静态显示一个URDF文件。

    :param urdf_filepath: 要加载的URDF文件的完整路径。
    """
    # 1. 初始化VPython场景
    # 我们先关闭可能存在的旧场景，确保每次调用函数都创建一个新窗口
    if vp.canvas.get_selected():
        vp.canvas.get_selected().delete()
        
    scene = vp.canvas(title=f"URDF Viewer: {urdf_filepath}", width=800, height=700, background=vp.color.gray(0.3))
    scene.camera.pos = vp.vector(1, 1, 2)
    scene.camera.axis = -vp.vector(1, 1, 2)
    
    # 创建一个坐标系轴，方便观察
    vp.arrow(pos=vp.vector(0,0,0), axis=vp.vector(0.5,0,0), color=vp.color.red, shaftwidth=0.01)
    vp.arrow(pos=vp.vector(0,0,0), axis=vp.vector(0,0.5,0), color=vp.color.green, shaftwidth=0.01)
    vp.arrow(pos=vp.vector(0,0,0), axis=vp.vector(0,0,0.5), color=vp.color.blue, shaftwidth=0.01)

    # 2. 使用ikpy加载URDF文件
    try:
        my_chain = ikpy.chain.Chain.from_urdf_file(urdf_filepath)
        print(f"成功加载模型: {urdf_filepath}")
        print(f"模型包含 {len(my_chain.links) - 1} 个活动连杆。")
    except FileNotFoundError:
        print(f"错误: URDF文件 '{urdf_filepath}' 未找到。")
        return

    # 3. 计算初始姿态 (所有关节角度为0)
    num_links = len(my_chain.links)
    initial_angles = [0] * num_links
    fk_results = my_chain.forward_kinematics(initial_angles, full_kinematics=True)

    # 4. 遍历ikpy的计算结果，并使用VPython进行绘制
    # ikpy链的第一个元素是代表世界原点的OriginLink，它没有实体，我们需要跳过它。
    # 我们直接从列表的第二个元素(索引为1)开始循环。
    for i, link in enumerate(my_chain.links[1:]):
        
        # 注意：因为我们的 link 循环是从 my_chain.links 的第二个元素开始的，
        # 所以 i 的值会从0开始。但对应的变换矩阵在 fk_results 列表中的索引需要加1才能匹配上。
        matrix = fk_results[i + 1]
        
        # --- 后续代码几乎不变 ---
        position = matrix[:3, 3]
        orientation_matrix = matrix[:3, :3]
        # 如果没有link.visuals这个属性，则跳过这个link
        if not hasattr(link, 'visuals') or not link.visuals:
            continue
        # 因为我们已经跳过了没有visuals的OriginLink，所以这里的link肯定有visuals
        visual = link.visuals[0]
        geometry = visual.geometry
        
        pos_vec = vp.vector(position[0], position[1], position[2])
        
        obj = None
        if isinstance(geometry, ikpy.geometry.Box):
            size = geometry.size
            obj = vp.box(pos=pos_vec, size=vp.vector(size[0], size[1], size[2]))
        elif isinstance(geometry, ikpy.geometry.Cylinder):
            length = geometry.length
            radius = geometry.radius
            obj = vp.cylinder(pos=pos_vec, length=length, radius=radius)
        elif isinstance(geometry, ikpy.geometry.Sphere):
            radius = geometry.radius
            obj = vp.sphere(pos=pos_vec, radius=radius)
            
        if obj:
            # 提取颜色，如果URDF中定义了
            if visual.color is not None:
                r, g, b, a = visual.color
                obj.color = vp.vector(r, g, b)
                obj.opacity = a

            # 应用连杆自身坐标系的旋转
            # 注意：VPython中cylinder的默认朝向是沿着X轴，我们URDF生成器里假设是Y轴或Z轴，
            # 为了统一，这里我们直接使用旋转矩阵来定义完整的坐标系
            x_axis = orientation_matrix @ np.array([1, 0, 0])
            y_axis = orientation_matrix @ np.array([0, 1, 0])
            z_axis = orientation_matrix @ np.array([0, 0, 1])
            
            obj.axis = vp.vector(z_axis[0], z_axis[1], z_axis[2]) * (obj.length if hasattr(obj, 'length') else 1)
            obj.up = vp.vector(y_axis[0], y_axis[1], y_axis[2])

            # URDF中visual的origin定义了视觉模型相对于连杆原点的偏移
            if visual.origin is not None:
                offset_pos = visual.origin[:3, 3]
                # 将这个偏移向量也根据连杆的姿态进行旋转
                rotated_offset = orientation_matrix @ offset_pos
                obj.pos += vp.vector(rotated_offset[0], rotated_offset[1], rotated_offset[2])

    print("模型已在窗口中显示。")
    print("这个窗口可以交互，用右键或中键拖动来旋转/缩放。")
    print("关闭可视化窗口即可结束程序。")
    
    # 保持窗口打开直到被关闭
    scene.waitfor('delete')
    print("可视化窗口已关闭。")


# --- 如何使用这个函数 ---

if __name__ == '__main__':
    # 当这个脚本被直接运行时，会执行下面的代码作为演示

    # 定义要加载的URDF文件名
    # 您可以把前一个脚本生成的 "humanoid_generated.urdf"放在同一个目录下
    urdf_to_view = "humanoid_generated.urdf"

    # 直接调用函数
    view_urdf_from_file(urdf_to_view)

    print("脚本执行完毕。")