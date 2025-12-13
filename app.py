import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# --- 1. 页面配置 ---
st.set_page_config(page_title="第33题动态演示", layout="wide")

# 解决中文显示问题 (Streamlit Cloud Linux环境通常没有黑体，这里使用通用字体回退方案)
plt.rcParams['font.sans-serif'] = ['sans-serif'] 
plt.rcParams['axes.unicode_minus'] = False

# --- 2. 核心数学逻辑 (保持不变) ---
def get_triangle_CDE(c, angle_deg):
    theta = np.radians(angle_deg)
    xc, yc = c, c
    xd = xc + 2 * np.cos(theta)
    yd = yc + 2 * np.sin(theta)
    theta_de = theta - np.pi/2
    xe = xd + 2 * np.cos(theta_de)
    ye = yd + 2 * np.sin(theta_de)
    return np.array([[xc, yc], [xd, yd], [xe, ye]])

def apply_n_transform(points, n, progress):
    trans_points = points.copy()
    if progress <= 0.5:
        # 翻折阶段
        t = progress / 0.5
        trans_points[:, 1] = points[:, 1] * (1 - t) + (2 * n - points[:, 1]) * t
    else:
        # 平移阶段
        trans_points[:, 1] = 2 * n - points[:, 1]
        t = (progress - 0.5) / 0.5
        trans_points[:, 0] = points[:, 0] + t * n
    return trans_points

def check_validity(points, c):
    # 稍微放宽一点精度，避免浮点数误差
    return points[1, 0] <= c + 1e-4 and points[2, 0] <= c + 1e-4

def calc_c_range(angle_deg, n):
    base_tri = get_triangle_CDE(0, angle_deg)
    sum_D = base_tri[1, 0] + base_tri[1, 1]
    sum_E = base_tri[2, 0] + base_tri[2, 1]
    c1 = (n - sum_D) / 2
    c2 = (n - sum_E) / 2
    return min(c1, c2), max(c1, c2)

# --- 3. 侧边栏控制区 ---
st.sidebar.header("🕹️ 控制面板")

# 1. 变换动画
prog = st.sidebar.slider("1. 变换进度 (n型变换)", 0.0, 1.0, 0.0, 0.01)

# 2. 几何参数
st.sidebar.markdown("---")
c = st.sidebar.slider("2. 点C位置 (参数 c)", -5.0, 8.0, 1.0, 0.1)
n = st.sidebar.slider("3. 参数 n", 1.0, 5.0, 3.0, 0.1)
angle = st.sidebar.slider("4. 旋转角度", 0.0, 360.0, 180.0, 5.0)

# --- 4. 主绘图区 ---
st.title("📐 第(3)问：n型对照变换与c的取值范围")
st.markdown("拖动左侧滑块，观察三角形的变化。")

# 创建图形
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect('equal')
ax.set_xlim(-6, 12)
ax.set_ylim(-6, 12)
ax.grid(True, linestyle='--', alpha=0.4)

# 绘制辅助线
ax.plot([-10, 20], [-10, 20], 'k--', linewidth=1, label='y=x')
ax.plot([-10, 20], [n, n], 'b-.', linewidth=1, label=f'y={n}')

# 计算数据
pts_orig = get_triangle_CDE(c, angle)
is_valid = check_validity(pts_orig, c)
pts_trans = apply_n_transform(pts_orig, n, prog)

# 绘制三角形
if is_valid:
    color_orig = 'purple'
    color_trans = 'green'
    alpha_trans = 0.6
    status_msg = "✅ 满足题意 (xD≤c, xE≤c)"
else:
    color_orig = 'gray'
    color_trans = 'gray'
    alpha_trans = 0.3
    status_msg = "❌ 不合题意 (存在点横坐标 > c)"

# 原三角形
poly_orig = Polygon(pts_orig, closed=True, fill=False, edgecolor=color_orig, linestyle='--', linewidth=1)
ax.add_patch(poly_orig)

# 变换后三角形
poly_trans = Polygon(pts_trans, closed=True, color=color_trans, alpha=alpha_trans)
ax.add_patch(poly_trans)

# 标注顶点
offset = 0.4
labels = ['C', 'D', 'E']
for i, p in enumerate(pts_orig):
    ax.text(p[0], p[1]+offset, labels[i], color=color_orig, fontsize=10, ha='center')

for i, p in enumerate(pts_trans):
    ax.text(p[0], p[1]-offset, labels[i]+"'", color='darkgreen' if is_valid else 'gray', fontsize=10, ha='center')

# 计算和绘制 c 的范围
c_min, c_max = calc_c_range(angle, n)
if is_valid:
    ax.plot([c_min, c_max], [c_min, c_max], 'r-', linewidth=4, alpha=0.5, label='c 可行范围')

# 判断交点
has_intersection = False
if prog >= 0.99:
    d_prime = pts_trans[1]
    e_prime = pts_trans[2]
    val_d = d_prime[1] - d_prime[0]
    val_e = e_prime[1] - e_prime[0]
    has_intersection = (val_d * val_e <= 0)

# 显示图例
ax.legend(loc='upper left')

# 在 Streamlit 中显示 Matplotlib 图形
st.pyplot(fig)

# --- 5. 文字信息反馈区 ---
col1, col2 = st.columns(2)
with col1:
    st.info(f"**当前状态**: {status_msg}")
    
    intersect_str = "等待变换完成..."
    if prog >= 0.99:
        intersect_str = "🔴 相交" if has_intersection else "🔵 不相交"
    st.write(f"**D'E' 与 y=x 关系**: {intersect_str}")

with col2:
    st.success(f"**c 的理论范围**: [{c_min:.2f}, {c_max:.2f}]")
    
    delta = 0.05
    if c_min - delta <= c <= c_max + delta:
         st.write(f"**当前 c = {c:.2f}** (在范围内 ✅)")
    else:
         st.write(f"**当前 c = {c:.2f}** (在范围外)")
