import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.signal import find_peaks
import numpy as np
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="IMU 数据平台", layout="wide")
st.title("🏃 IMU 数据可视化与跑姿异常分析平台")

# 上传数据
uploaded_file = st.file_uploader("📁 上传 IMU 数据文件（CSV）", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success(f"文件已加载，共 {len(df)} 行")

    tab1, tab2, tab3 = st.tabs(["🧭 姿态分析", "👟 步态分析", "🎥 动作捕捉分析"])

    with tab1:
        locations = df["location"].unique()
        selected_location = st.selectbox("选择位置", locations)
        selected_channel = st.radio("选择通道", ["acc", "gyro"])

        df_selected = df[(df["location"] == selected_location) & (df["channel"] == selected_channel)]

        st.subheader(f"📉 {selected_channel.upper()} 三轴数据")
        fig1 = px.line(df_selected, x="timestamp", y=["value_x", "value_y", "value_z"],
                       labels={"value_x": "X", "value_y": "Y", "value_z": "Z"})
        st.plotly_chart(fig1, use_container_width=True)

        if {"roll", "pitch", "yaw"}.issubset(df.columns):
            st.subheader("🎯 姿态角（Roll, Pitch, Yaw）")
            df_pose = df[df["channel"] == "acc"]
            fig2 = px.line(df_pose, x="timestamp", y=["roll", "pitch", "yaw"])
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        df_pose = df[(df["channel"] == "acc") & (df["location"] == selected_location)]

        st.subheader("👟 步态周期检测（以 acc.z 为例）")
        acc_z = df_pose["value_z"].to_numpy()
        timestamps = df_pose["timestamp"].to_numpy()
        peaks, _ = find_peaks(acc_z, prominence=0.5, distance=20)
        st.info(f"检测到步数：{len(peaks)}")

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=timestamps, y=acc_z, name="acc.z"))
        fig3.add_trace(go.Scatter(x=timestamps[peaks], y=acc_z[peaks],
                                  mode='markers', marker=dict(color='red', size=8),
                                  name='步态起点'))
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("🚨 姿态异常检测（Pitch > 20°）")
        df_pitch = df_pose[["timestamp", "pitch"]].copy()
        threshold = 20
        df_pitch["is_abnormal"] = df_pitch["pitch"].abs() > threshold
        abnormal_times = df_pitch[df_pitch["is_abnormal"]]["timestamp"].tolist()
        st.markdown(f"**异常时刻数**: {len(abnormal_times)}")
        if abnormal_times:
            st.warning(f"异常示例（前5个）：{abnormal_times[:5]}")

        fig4 = px.line(df_pitch, x="timestamp", y="pitch", title="Pitch 姿态角与异常点")
        fig4.add_scatter(x=df_pitch[df_pitch["is_abnormal"]]["timestamp"],
                         y=df_pitch[df_pitch["is_abnormal"]]["pitch"],
                         mode='markers', marker=dict(color='red'), name="异常点")
        st.plotly_chart(fig4, use_container_width=True)

    with tab3:
        st.subheader("🎞️ 动作回放（姿态角 + Stick Figure）")

        location_options = df["location"].unique().tolist()
        loc_selected = st.selectbox("🎯 选择回放部位", location_options)
        df_one = df[(df["location"] == loc_selected) & (df["channel"] == "acc")].copy()

        frame = st.slider("选择时间帧", 0, len(df_one)-1, 0, step=1)
        current = df_one.iloc[frame]

        st.write(f"🧍 时间: {current['timestamp']} ms")
        st.metric("Roll", f"{current['roll']:.2f}°")
        st.metric("Pitch", f"{current['pitch']:.2f}°")
        st.metric("Yaw", f"{current['yaw']:.2f}°")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_one['timestamp'], y=df_one['roll'], name="Roll"))
        fig.add_trace(go.Scatter(x=df_one['timestamp'], y=df_one['pitch'], name="Pitch"))
        fig.add_trace(go.Scatter(x=df_one['timestamp'], y=df_one['yaw'], name="Yaw"))
        fig.add_vline(x=current["timestamp"], line_dash="dot", line_color="red", name="当前帧")
        st.plotly_chart(fig, use_container_width=True)

        def draw_stick_figure(pitch_deg):
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.set_xlim(-1, 1)
            ax.set_ylim(-0.2, 2)
            ax.axis('off')
            hip = [0, 1.5]
            shoulder = [0, 1.9]
            ax.plot([hip[0], shoulder[0]], [hip[1], shoulder[1]], 'k-', lw=4)
            thigh_end = [0, 1.0]
            ax.plot([hip[0], thigh_end[0]], [hip[1], thigh_end[1]], 'r-', lw=4)
            length = 0.5
            theta = np.deg2rad(pitch_deg)
            knee_x, knee_y = thigh_end
            ankle_x = knee_x + length * np.sin(theta)
            ankle_y = knee_y - length * np.cos(theta)
            ax.plot([knee_x, ankle_x], [knee_y, ankle_y], 'b-', lw=4)
            ax.plot(*hip, 'ko', markersize=8)
            ax.plot(*thigh_end, 'ko', markersize=8)
            ax.plot(ankle_x, ankle_y, 'ko', markersize=8)
            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            plt.close(fig)
            return buf

        st.subheader("🦿 Stick Figure 渲染图")
        fig_buf = draw_stick_figure(current["pitch"])
        st.image(fig_buf, caption=f"Pitch = {current['pitch']:.2f}°")
else:
    st.warning("请上传 CSV 文件以开始分析。")
