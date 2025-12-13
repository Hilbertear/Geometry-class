import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 (强制宽屏) ---
st.set_page_config(
    page_title="几何变换探究",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 (与你提供的 Matplotlib 逻辑完全一致) ---

def get_triangle_CDE(c, angle_deg):
    """计算原始三角形 CDE 的坐标"""
    theta = np.radians(angle_deg)
    xc, yc = c, c
    xd = xc + 2 * np.cos(theta)
    yd = yc + 2 * np.sin(theta)
    theta_de = theta - np.pi/2
    xe = xd + 2 * np.cos(theta_de)
    ye = yd + 2 * np.sin(theta_de)
    return np.array([[xc, yc], [xd, yd], [xe, ye]])

def apply_n_transform(points, n, progress):
    """
    n型变换逻辑:
    0~0.5: 关于 y=n 翻折 (对称)
    0.5~1.0: 向右平移 n
    """
    trans_points = points.copy()
    if progress <= 0.5:
        # 阶段一：翻折 (对称)
        t = progress / 0.5
        # y' = y(1-t) + (2n-y)t
        trans_points[:, 1] = points[:, 1] * (1 - t) + (2 * n - points[:, 1]) * t
    else:
        # 阶段二：平移
        trans_points[:, 1] = 2 * n - points[:, 1] # 确保翻折完成
        t = (progress - 0.5) / 0.5
        trans_points[:, 0] = points[:, 0] + t * n
    return trans_points

def check_intersection(points):
    """判断线段 D'E' 是否与 y=x 相交 (异号即相交)"""
    D_prime = points[1]
    E_prime = points[2]
    # 直线方程 f(x,y) = y - x. 代入两点坐标
    val_D = D_prime[1] - D_prime[0]
    val_E = E_prime[1] - E_prime[0]
    return (val_D * val_E <= 0)

def calc_c_range(angle_deg, n):
    """计算 c 的可行范围"""
    base_tri = get_triangle_CDE(0, angle_deg)
    sum_D = base_tri[1, 0] + base_tri[1, 1]
    sum_E = base_tri[2, 0] + base_tri[2, 1]
    c1 = (n - sum_D) / 2
    c2 = (n - sum_E) / 2
    return min(c1, c2), max(c1, c2)

# --- 3. 侧边栏控制 ---
with st.sidebar:
    st.header("🎛️ 探究控制台")
    st.info("💡 提示：先将进度条拖到最右侧，再调整参数观察相交情况。")
    
    # 动画进度
    progress = st.slider("▶️ 变换进度 (0.0=原图, 0.5=对称, 1.0=完成)", 0.0, 1.0, 0.0, 0.01)
    
    st.divider()
    
    # 核心参数
    c_val = st.slider("🅰️ 点 C 位置 (c)", -5.0, 8.0, 1.0, 0.1)
    n_val = st.slider("🅱️ 参数 n (对称轴 y=n)", 1.0, 5.0, 3.0, 0.1)
    angle_val = st.slider("🔄 旋转角度", 0, 360, 180, 5)

# --- 4. 数据计算 ---
pts_orig = get_triangle_CDE(c_val, angle_val)
pts_trans = apply_n_transform(pts_orig, n_val, progress)

# 闭合多边形用于画图
def close_polygon(pts):
    return np.vstack([pts, pts[0]])

plot_orig = close_polygon(pts_orig)
plot_trans = close_polygon(pts_trans)

# 判断逻辑
is_valid = (pts_orig[1, 0] <= c_val + 1e-5) and (pts_orig[2, 0] <= c_val + 1e-5)
has_intersect = check_intersection(pts_trans)
c_min, c_max = calc_c_range(angle_val, n_val)

# --- 5. 显示状态信息 ---
st.title("📐 n型变换与交点探究 (教室模式)")

col1, col2 = st.columns(2)
with col1:
    if is_valid:
        st.success(f"✅ 原始图形：满足 xd, xe ≤ c")
    else:
        st.error(f"❌ 原始图形：不合题意 (须 xd, xe ≤ c)")

with col2:
    if progress >= 0.99:
        if has_intersect:
            st.error(f"🔴 状态：D'E' 与 y=x **相交**")
        else:
            st.info(f"🔵 状态：D'E' 与 y=x **不相交**")
    else:
        st.warning("⚠️ 变换进行中... (请拖动进度条到最右侧)")

st.markdown(f"**📊 理论计算：** 当前角度下，使变换后相交的 $c$ 的范围是 **$[{c_min:.2f}, {c_max:.2f}]$**")

# --- 6. Plotly 画图 (强制白底黑字) ---
fig = go.Figure()

# [图层1] 辅助线 y=x
fig.add_trace(go.Scatter(
    x=[-10, 20], y=[-10, 20],
    mode='lines', name='y=x',
    line=dict(color='black', width=1, dash='dash'), # 黑色虚线
    hoverinfo='skip'
))

# [图层2] 对称轴 y=n
fig.add_trace(go.Scatter(
    x=[-10, 20], y=[n_val, n_val],
    mode='lines', name=f'对称轴 y={n_val}',
    line=dict(color='blue', width=2, dash='dashdot'),
    hoverinfo='skip'
))

# [图层3] 原始三角形 (紫色虚线)
fig.add_trace(go.Scatter(
    x=plot_orig[:, 0], y=plot_orig[:, 1],
    mode='lines+markers+text',
    name='原三角形',
    line=dict(color='purple', width=2, dash='dot'),
    marker=dict(size=6, color='purple'),
    text=["<b>C</b>", "<b>D</b>", "<b>E</b>", ""], 
    textposition="top left",
    textfont=dict(size=16, color='purple')
))

# [图层4] 变换后三角形 (绿色填充)
fig.add_trace(go.Scatter(
    x=plot_trans[:, 0], y=plot_trans[:, 1],
    mode='lines+markers+text',
    name='变换后三角形',
    fill='toself', fillcolor='rgba(0, 200, 100, 0.3)',
    line=dict(color='green', width=3),
    marker=dict(size=8, color='green'),
    text=["<b>C'</b>", "<b>D'</b>", "<b>E'</b>", ""], 
    textposition="bottom right",
    textfont=dict(size=16, color='darkgreen')
))

# [图层5] D'E' 线段高亮
de_color = 'red' if has_intersect and progress > 0.9 else 'green'
fig.add_trace(go.Scatter(
    x=[pts_trans[1,0], pts_trans[2,0]], 
    y=[pts_trans[1,1], pts_trans[2,1]],
    mode='lines', name="D'E'线段",
    line=dict(color=de_color, width=4),
    hoverinfo='skip'
))

# --- 7. 画布布局 (教科书风格) ---
fig.update_layout(
    # 强制白色背景
    paper_bgcolor='white',
    plot_bgcolor='white',
    template="simple_white",
    
    height=700,
    
    # 标题
    title=dict(
        text="<b>几何变换平面直角坐标系</b>",
        font=dict(size=22, color="black"),
        x=0.5
    ),
    
    # X轴设置
    xaxis=dict(
        title=dict(text="<b>x 轴</b>", font=dict(size=18, color="black")),
        range=[-6, 15], 
        zeroline=True, zerolinewidth=2, zerolinecolor='black', # 坐标轴线加粗变黑
        gridcolor='lightgray', gridwidth=1, showgrid=True,
        tickfont=dict(size=14, color="black")
    ),
    
    # Y轴设置
    yaxis=dict(
        title=dict(text="<b>y 轴</b>", font=dict(size=18, color="black")),
        range=[-6, 12], 
        scaleanchor="x", scaleratio=1,
        zeroline=True, zerolinewidth=2, zerolinecolor='black',
        gridcolor='lightgray', gridwidth=1, showgrid=True,
        tickfont=dict(size=14, color="black")
    ),
    
    # 图例设置
    legend=dict(
        x=0.01, y=0.99,
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="black", borderwidth=1,
        font=dict(size=14, color="black")
    ),
    
    dragmode="pan"
)

st.plotly_chart(fig, use_container_width=True)
