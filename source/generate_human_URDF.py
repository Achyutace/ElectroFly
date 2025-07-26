import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import math

def prettify(elem):
    """返回一个带缩进的美化后的XML字符串"""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_link(name, material_name):
    """
    创建一个<link>元素，并引用一个已定义的全局材质。
    """
    link = ET.Element('link', name=name)
    
    # --- Visual part ---
    visual = ET.SubElement(link, 'visual')
    geometry = ET.SubElement(visual, 'geometry')
    ET.SubElement(visual, 'material', name=material_name)
    
    # --- Inertial part (for physics) ---
    inertial = ET.SubElement(link, 'inertial')
    ET.SubElement(inertial, 'origin', xyz="0 0 0", rpy="0 0 0")
    ET.SubElement(inertial, 'mass', value="1.0")
    ET.SubElement(inertial, 'inertia', ixx="0.01", ixy="0", ixz="0", iyy="0.01", iyz="0", izz="0.01")
    
    return link, visual, geometry

def create_joint(name, type, parent, child, origin_xyz="0 0 0", origin_rpy="0 0 0", axis="1 0 0", limits=None):
    """
    创建一个<joint>元素。
    现在可以接收并应用特定的关节限制。
    """
    joint = ET.Element('joint', name=name, type=type)
    ET.SubElement(joint, 'parent', link=parent)
    ET.SubElement(joint, 'child', link=child)
    ET.SubElement(joint, 'origin', xyz=origin_xyz, rpy=origin_rpy)
    if type != "fixed":
        ET.SubElement(joint, 'axis', xyz=axis)
        
        # 如果没有提供特定限制，则使用默认的通用限制
        if limits is None:
            limits = {'lower': -math.pi, 'upper': math.pi}
            
        ET.SubElement(joint, 'limit', 
                      lower=str(limits['lower']),
                      upper=str(limits['upper']),
                      effort="100.0",
                      velocity="10.0")
    return joint

def generate_urdf(height_m, filename="humanoid.urdf"):
    """
    根据身高生成一个人形骨架的URDF文件
    :param height_m: 用户身高（单位：米）
    :param filename: 输出的URDF文件名
    """
    
    proportions = {
        'pelvis_width': 0.17 * height_m,
        'torso_height': 0.33 * height_m,
        'head_radius': (0.13 * height_m) / 2,
        'upper_arm_length': 0.186 * height_m,
        'forearm_length': 0.146 * height_m,
        'thigh_length': 0.245 * height_m,
        'thigh_radius': 0.05,
        'shank_length': 0.246 * height_m,
        'shank_radius': 0.04,
        'foot_length': 0.15 * height_m,
        'foot_height': 0.04,
    }

    # --- 定义符合人体工程学的关节角度限制 (单位: 度) ---
    joint_limits_deg = {
        "head":       {'lower': -90, 'upper': 90},
        "shoulder":   {'lower': -90, 'upper': 120},
        "elbow":      {'lower': 0,   'upper': 150},
        "hip":        {'lower': -80, 'upper': 30},
        "knee":       {'lower': 0,   'upper': 140},
        # ✅ 核心改动: 限制脚踝的运动范围，使其更符合自然步态
        "ankle":      {'lower': -20, 'upper': 20},
    }

    # --- 将角度转换为弧度 ---
    joint_limits_rad = {
        key: {'lower': math.radians(val['lower']), 'upper': math.radians(val['upper'])}
        for key, val in joint_limits_deg.items()
    }


    robot = ET.Element('robot', name="Humanoid")

    # --- 定义全局材质 ---
    materials = {
        "yellow": "0.9 0.9 0 1", "green": "0.1 0.8 0.1 1", "pink": "0.9 0.5 0.5 1",
        "red": "1 0 0 1", "blue": "0 0 1 1", "red_tint": "1 0.5 0.5 1",
        "blue_tint": "0.5 0.5 1 1", "grey": "0.5 0.5 0.5 1", "cyan_sensor": "0 1 1 1"
    }
    for name, rgba in materials.items():
        mat = ET.SubElement(robot, 'material', name=name)
        ET.SubElement(mat, 'color', rgba=rgba)

    # --- 创建连杆 (Links) ---

    base_link = ET.SubElement(robot, 'link', name="base_link")
    base_inertial = ET.SubElement(base_link, 'inertial')
    ET.SubElement(base_inertial, 'mass', value="0.01")
    ET.SubElement(base_inertial, 'inertia', ixx="0.0001", ixy="0", ixz="0", iyy="0.0001", iyz="0", izz="0.0001")

    pelvis, _, pelvis_geom = create_link("pelvis", material_name="yellow")
    ET.SubElement(pelvis_geom, 'box', size=f"0.05 {proportions['pelvis_width']} 0.05")
    robot.append(pelvis)

    torso, torso_visual, torso_geom = create_link("torso", material_name="green")
    ET.SubElement(torso_geom, 'box', size=f"{proportions['pelvis_width']*0.7} {proportions['pelvis_width']*0.9} {proportions['torso_height']}")
    ET.SubElement(torso_visual, 'origin', xyz=f"0 0 {proportions['torso_height']/2}", rpy="0 0 0")
    robot.append(torso)

    head, head_visual, head_geom = create_link("head", material_name="pink")
    ET.SubElement(head_geom, 'sphere', radius=f"{proportions['head_radius']}")
    ET.SubElement(head_visual, 'origin', xyz=f"0 0 {proportions['head_radius']}", rpy="0 0 0")
    robot.append(head)

    # --- 创建关节 (Joints) ---
    
    pelvis_joint = create_joint("pelvis_joint", "fixed", "base_link", "pelvis", origin_xyz=f"0 0 {proportions['thigh_length'] + proportions['shank_length']}")
    robot.append(pelvis_joint)

    torso_joint = create_joint("torso_joint", "fixed", "pelvis", "torso")
    robot.append(torso_joint)

    head_joint = create_joint("head_joint", "revolute", "torso", "head", 
                              origin_xyz=f"0 0 {proportions['torso_height']}",
                              axis="0 0 1",
                              limits=joint_limits_rad['head'])
    robot.append(head_joint)

    # --- 循环创建四肢 ---
    for side in ['r', 'l']:
        side_mult = 1 if side == 'r' else -1
        
        thigh_color = "red" if side == 'r' else "blue"
        shank_color = "red_tint" if side == 'r' else "blue_tint"

        # 大腿 (Thigh)
        thigh, thigh_visual, thigh_geom = create_link(f"thigh_{side}", material_name=thigh_color)
        ET.SubElement(thigh_geom, 'cylinder', length=f"{proportions['thigh_length']}", radius=f"{proportions['thigh_radius']}")
        ET.SubElement(thigh_visual, 'origin', xyz=f"0 0 {-proportions['thigh_length']/2}", rpy="0 0 0")
        robot.append(thigh)
        
        # 修正髋关节轴向，实现前后摆动
        hip_joint = create_joint(f"hip_{side}", "revolute", "pelvis", f"thigh_{side}",
                                 origin_xyz=f"0 {side_mult * proportions['pelvis_width']/2} 0",
                                 axis="0 1 0",
                                 limits=joint_limits_rad['hip'])
        robot.append(hip_joint)

        # 大腿传感器
        thigh_sensor, _, thigh_sensor_geom = create_link(f"thigh_sensor_{side}", "cyan_sensor")
        ET.SubElement(thigh_sensor_geom, 'box', size="0.01 0.01 0.01")
        robot.append(thigh_sensor)
        thigh_sensor_joint = create_joint(f"thigh_sensor_joint_{side}", "fixed", f"thigh_{side}", f"thigh_sensor_{side}",
                                          origin_xyz=f"{-proportions['thigh_radius']} 0 {-proportions['thigh_length']/2}")
        robot.append(thigh_sensor_joint)
        
        # 小腿 (Shank)
        shank, shank_visual, shank_geom = create_link(f"shank_{side}", material_name=shank_color)
        ET.SubElement(shank_geom, 'cylinder', length=f"{proportions['shank_length']}", radius=f"{proportions['shank_radius']}")
        ET.SubElement(shank_visual, 'origin', xyz=f"0 0 {-proportions['shank_length']/2}", rpy="0 0 0")
        robot.append(shank)

        # 修正膝关节轴向，实现前后弯曲
        knee_joint = create_joint(f"knee_{side}", "revolute", f"thigh_{side}", f"shank_{side}",
                                  origin_xyz=f"0 0 {-proportions['thigh_length']}",
                                  axis="0 1 0",
                                  limits=joint_limits_rad['knee'])
        robot.append(knee_joint)

        # 小腿传感器
        shank_sensor, _, shank_sensor_geom = create_link(f"shank_sensor_{side}", "cyan_sensor")
        ET.SubElement(shank_sensor_geom, 'box', size="0.01 0.01 0.01")
        robot.append(shank_sensor)
        shank_sensor_joint = create_joint(f"shank_sensor_joint_{side}", "fixed", f"shank_{side}", f"shank_sensor_{side}",
                                          origin_xyz=f"{-proportions['shank_radius']} 0 {-proportions['shank_length']/2}")
        robot.append(shank_sensor_joint)

        # 脚 (Foot)
        foot, foot_visual, foot_geom = create_link(f"foot_{side}", material_name="grey")
        ET.SubElement(foot_geom, 'box', size=f"{proportions['foot_length']} {proportions['pelvis_width']*0.4} {proportions['foot_height']}")
        ET.SubElement(foot_visual, 'origin', xyz=f"{proportions['foot_length']/2} 0 {-proportions['foot_height']/2}", rpy="0 0 0")
        robot.append(foot)

        # 脚踝关节轴向 (0 1 0) 是正确的，用于上下勾脚
        ankle_joint = create_joint(f"ankle_{side}", "revolute", f"shank_{side}", f"foot_{side}",
                                   origin_xyz=f"0 0 {-proportions['shank_length']}",
                                   axis="0 1 0",
                                   limits=joint_limits_rad['ankle'])
        robot.append(ankle_joint)

        # 脚背传感器
        foot_sensor, _, foot_sensor_geom = create_link(f"foot_sensor_{side}", "cyan_sensor")
        ET.SubElement(foot_sensor_geom, 'box', size="0.01 0.01 0.01")
        robot.append(foot_sensor)
        foot_sensor_joint = create_joint(f"foot_sensor_joint_{side}", "fixed", f"foot_{side}", f"foot_sensor_{side}",
                                         origin_xyz=f"{proportions['foot_length']/2} 0 {proportions['foot_height']/2}")
        robot.append(foot_sensor_joint)

        # 大臂 (Upper Arm)
        upper_arm, upper_arm_visual, upper_arm_geom = create_link(f"upper_arm_{side}", material_name=thigh_color)
        ET.SubElement(upper_arm_geom, 'cylinder', length=f"{proportions['upper_arm_length']}", radius="0.04")
        ET.SubElement(upper_arm_visual, 'origin', xyz=f"0 0 {-proportions['upper_arm_length']/2}", rpy="0 0 0")
        robot.append(upper_arm)

        # 修正肩关节轴向，实现前后摆臂
        shoulder_joint = create_joint(f"shoulder_{side}", "revolute", "torso", f"upper_arm_{side}",
                                      origin_xyz=f"0 {side_mult * (proportions['pelvis_width']/2 * 0.9)} {proportions['torso_height'] - 0.05}",
                                      axis="0 1 0",
                                      limits=joint_limits_rad['shoulder'])
        robot.append(shoulder_joint)

        # 小臂 (Forearm)
        forearm, forearm_visual, forearm_geom = create_link(f"forearm_{side}", material_name=shank_color)
        ET.SubElement(forearm_geom, 'cylinder', length=f"{proportions['forearm_length']}", radius="0.03")
        ET.SubElement(forearm_visual, 'origin', xyz=f"0 0 {-proportions['forearm_length']/2}", rpy="0 0 0")
        robot.append(forearm)

        # 修正肘关节轴向，实现前后弯曲
        elbow_joint = create_joint(f"elbow_{side}", "revolute", f"upper_arm_{side}", f"forearm_{side}",
                                   origin_xyz=f"0 0 {-proportions['upper_arm_length']}",
                                   axis="0 1 0",
                                   limits=joint_limits_rad['elbow'])
        robot.append(elbow_joint)

    # --- 保存到文件 ---
    xml_str = prettify(robot)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"成功生成URDF文件: {filename}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="根据身高生成人形骨架URDF文件。")
    parser.add_argument("--height", type=float, default=1.75, help="用户身高（单位：米）。")
    parser.add_argument("--output", type=str, default="humanoid_generated.urdf", help="输出的URDF文件名。")
    
    args = parser.parse_args()
    
    generate_urdf(args.height, args.output)
