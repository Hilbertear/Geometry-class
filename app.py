import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面基础配置 ---
st.set_page_config(
    page_title="n型变换探究", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 (移植自你的 Matplotlib 代码) ---

def get_triangle_CDE(c, angle_deg):
    """计算原始三角形 CDE 的坐标"""
    theta = np.radians(angle_deg)
    xc, yc = c, c
    xd = xc + 2 * np.cos(theta)
    yd = yc + 2 * np.sin(theta)
    theta_de = theta - np.pi/2
    xe = xd + 2 * np.cos(theta_de)
    ye = yd + 2 * np.sin(theta_de)
    # 返回形状为 (3, 2) 的数组
    return np.array([[xc, yc], [xd, yd], [xe, ye]])

def apply_n_transform(points, n, progress):
    """
    执行 n 型变换动画逻辑
    0~0.5: 关于 y=n 做轴对称 (翻折)
    0.5~1.0: 向右平移 n
    """
    trans_points = points.copy()
    if progress <= 0.5:
        # 阶段一：翻折 (Visualizing Reflection)
        # 归一化时间 t (0~1)
        t = progress / 0.5
        # 线性插值：从 y 变到 2n-y
        # y' = y(1-t) + (2n-y)t
        trans_points[:, 1] = points[:, 1] * (1 - t) + (2 * n - points[:, 1]) * t
    else:
        # 阶段二：平移 (Translation)
        # 先完成翻折
        trans_points[:, 1] = 2 * n - points[:, 1]
        # 再进行平移
        t = (progress - 0.5) / 0.5
        trans_points[:, 0] = points[:, 0] + t * n
    return trans_points

def check_intersection(points):
    """判断线段 D'E' 是否与 y=x 相交"""
    # points 是变换后的 [C', D', E']
    D_prime = points[1]
    E_prime = points[2]
    
    # y=x 可以写成 F(x,y) = y - x = 0
    # 如果两个点代入 F(x,y) 异号，说明在直线两侧
    val_D = D_prime[1] - D_prime[0]
    val_E = E_prime[1] - E_prime[0]
    
    # 乘积小于等于0说明异号或在直线上
    return (val_D * val_E <= 0)

def calc_c_range(angle_deg, n):
    """计算 c 的可行范围 (照搬原逻辑)"""
    base_tri = get_triangle_CDE(0, angle_deg)
    # 原逻辑似乎是基于 x_D <= c 和 x_E <= c 推导
    # x_D = c + delta_xD -> c + delta_xD <= c -> delta_xD <= 0? 
    # 你原来的代码逻辑：c1 = (n - sum_D)/2 ... 这里的推导比较特定，我直接复用你的公式
    sum_D = base_tri[1, 0] + base_tri[1, 1]
    sum_E = base_tri[2, 0] + base_tri[2, 1]
    c1 = (n - sum_D) / 2
    c2 = (n - sum_E) / 2
    return min(c1, c2), max(c1, c2)

# --- 3. 侧边栏控制 ---
with st.sidebar:
    st.header("🎛️ 探究控制台")
    
    # 动画进度滑块
    progress = st.slider("▶️ 变换进度 (0.0=原图, 0.5=对称, 1.0=完成)", 0.0, 1.0, 0.0, 0.01)
    
    st.divider()
    
    # 参数滑块
    c_val = st.slider("🅰️ 点 C 位置 (c)", -5.0, 8.0, 1.0, 0.1)
    n_val = st.slider("🅱️ 参数 n (对称轴 y=n)", 1.0, 5.0, 3.0, 0.1)
    angle_val = st.slider("🔄 旋转角度", 0, 360, 180, 5)

# --- 4. 数据计算 ---
# 1. 获取原始坐标
pts_orig = get_triangle_CDE(c_val, angle_val)

# 2. 获取变换后坐标
pts_trans = apply_n_transform(pts_orig, n_val, progress)

# 3. 构造闭合多边形用于画图 (C-D-E-C)
def close_polygon(pts):
    return np.vstack([pts, pts[0]])

plot_orig = close_polygon(pts_orig)
plot_trans = close_polygon(pts_trans)

# 4. 判断逻辑
# 有效性判断 (xD <= c 且 xE <= c) ? 
# 注意：你的原代码 logic 是 points[1,0] <= c... 但在 get_triangle 里 xd = c + ... 
# 所以这实际上是判断 D, E 是否在 C 的左侧/竖直线上
is_valid = (pts_orig[1, 0] <= c_val + 1e-5) and (pts_orig[2, 0] <= c_val + 1e-5)

# 相交判断
has_intersect = check_intersection(pts_trans)
c_min, c_max = calc_c_range(angle_val, n_val)

# --- 5. 状态信息显示区 ---
col1, col2 = st.columns(2)
with col1:
    if is_valid:
        st.success(f"✅ 原始图形位置：满足题意")
    else:
        st.error(f"❌ 原始图形位置：不合题意 (须 $x_D, x_E \le c$)")

with col2:
    if progress >= 0.9:
        if has_intersect:
            st.error(f"🔴 D'E' 与 y=x 相交！")
        else:
            st.info(f"🔵 D'E' 与 y=x 不相交")
    else:
        st.warning("⚠️ 变换进行中...完成变换后判断相交")

# 显示计算出的 c 范围
st.markdown(f"**🧮 理论计算：当前角度下，使变换后相交的 $c$ 的范围是 $[{c_min:.2f}, {c_max:.2f}]$**")


# --- 6. Plotly 画图 ---
fig = go.Figure()

# [图层1] 辅助线 y=x
fig.add_trace(go.Scatter(
    x=[-10, 20], y=[-10, 20],
    mode='lines', name='y=x',
    line=dict(color='gray', width=2, dash='dash'), hoverinfo='skip'
))

# [图层2] 对称轴 y=n (关键！展示翻折轴)
fig.add_trace(go.Scatter(
    x=[-10, 20], y=[n_val, n_val],
    mode='lines', name=f'对称轴 y={n_val}',
    line=dict(color='blue', width=2, dash='dashdot'), hoverinfo='skip'
))

# [图层3] 原始三角形 (紫色虚线)
fig.add_trace(go.Scatter(
    x=plot_orig[:, 0], y=plot_orig[:, 1],
    mode='lines+markers+text',
    name='原三角形',
    line=dict(color='purple', width=2, dash='dot'),
    marker=dict(size=6, color='purple'),
    text=["C", "D", "E", ""], textposition="top left",
    textfont=dict(size=14, color='purple')
))

# [图层4] 变换后三角形 (绿色填充)
fig.add_trace(go.Scatter(
    x=plot_trans[:, 0], y=plot_trans[:, 1],
    mode='lines+markers+text',
    name='变换后三角形',
    fill='toself', fillcolor='rgba(0, 200, 100, 0.4)',
    line=dict(color='green', width=3),
    marker=dict(size=8, color='green'),
    text=["<b>C'</b>", "<b>D'</b>", "<b>E'</b>", ""], 
    textposition="bottom right",
    textfont=dict(size=16, color='darkgreen')
))

# [图层5] 高亮 D'E' 线段 (如果相交则变红)
de_color = 'red' if has_intersect and progress > 0.9 else 'green'
fig.add_trace(go.Scatter(
    x=[pts_trans[1,0], pts_trans[2,0]], 
    y=[pts_trans[1,1], pts_trans[2,1]],
    mode='lines',
    name="D'E'线段",
    line=dict(color=de_color, width=4),
    hoverinfo='skip'
))


# --- 7. 画布布局 ---
fig.update_layout(
    template="simple_white",
    height=700,
    title=dict(
        text="<b>n型变换动态探究系统</b>", 
        font=dict(size=22)
    ),
    xaxis=dict(
        title="x", range=[-6, 12], 
        zeroline=True, zerolinewidth=2, zerolinecolor='black',
        gridcolor='lightgray'
    ),
    yaxis=dict(
        title="y", range=[-6, 12], 
        scaleanchor="x", scaleratio=1,
        zeroline=True, zerolinewidth=2, zerolinecolor='black',
        gridcolor='lightgray'
    ),
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)')
)

st.plotly_chart(fig, use_container_width=True)
