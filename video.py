import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="n型变换：环形区域探究",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 ---
# 固定 n=3
FIXED_N = 3.0

def get_circle_points(center_x, center_y, radius, steps=100):
    """生成圆的坐标点"""
    theta = np.linspace(0, 2*np.pi, steps)
    x = center_x + radius * np.cos(theta)
    y = center_y + radius * np.sin(theta)
    return x, y

def get_triangle_CDE(c, angle_deg, n):
    theta = np.radians(angle_deg)
    # n型变换后的 C' 坐标: (c+n, 2n-c)
    xc_prime = c + n
    yc_prime = 2 * n - c
    
    # 相对于 C' 的旋转 (注意：变换后的长度不变，形状不变)
    # CD=2, DE=2, CE=2sqrt(2). D'E' 也就是变换后的相应点
    # D' 相对于 C' 的位置
    xd_rel = 2 * np.cos(theta)
    yd_rel = 2 * np.sin(theta)
    
    # E' 相对于 C' 的位置 (顺时针旋转90度后，长度延伸到 2sqrt(2)? 不，题目是 CD=DE=2)
    # 也就是 E 在 D 的基础上再走一段。
    # 向量 CD = (2cos, 2sin). 向量 DE 垂直于 CD 且长度为 2.
    # 顺时针排列 C, D, E -> E 在 D 的 "右侧" (相对于 CD 方向顺时针转90度)
    # 向量 DE 方向: theta - 90度
    theta_de = theta - np.pi/2
    xe_rel = xd_rel + 2 * np.cos(theta_de)
    ye_rel = yd_rel + 2 * np.sin(theta_de)
    
    # 绝对坐标
    C_prime = np.array([xc_prime, yc_prime])
    D_prime = C_prime + np.array([xd_rel, yd_rel])
    E_prime = C_prime + np.array([xe_rel, ye_rel])
    
    return np.array([C_prime, D_prime, E_prime])

# --- 3. 侧边栏控制 ---
with st.sidebar:
    st.header("🎮 探究控制台")
    st.info("当前固定 $n=3$")
    
    # 唯一的自由度 c
    c_val = st.slider("🅰️ 拖动点 C' (改变参数 c)", -5.0, 5.0, 1.0, 0.1)
    
    st.divider()
    
    st.markdown("### 辅助设置")
    # 虽然只保留一个自由度，但为了演示"扫过"的效果，保留角度滑块作为演示辅助，或者自动播放
    show_sample_tri = st.checkbox("显示示例三角形 D'E'", value=True)
    angle_val = st.slider("示例三角形旋转角度", 0, 360, 45, 5, disabled=not show_sample_tri)

# --- 4. 计算绘图数据 ---
# C' 坐标
cx_prime = c_val + FIXED_N
cy_prime = 2 * FIXED_N - c_val

# 半径定义
r_inner = 2.0               # D' 的轨迹半径 (|CD|)
r_outer = np.sqrt(2**2 + 2**2) # E' 的轨迹半径 (|CE| = 2sqrt(2) approx 2.828)

# 生成圆环填充数据 (利用 Plotly 的 path 技巧实现带孔多边形)
theta = np.linspace(0, 2*np.pi, 120)
# 外圆 (顺时针)
x_out = cx_prime + r_outer * np.cos(theta)
y_out = cy_prime + r_outer * np.sin(theta)
# 内圆 (逆时针 - 用于挖洞)
x_in = cx_prime + r_inner * np.cos(theta[::-1])
y_in = cy_prime + r_inner * np.sin(theta[::-1])
# 合并路径
x_poly = np.concatenate([x_out, x_in])
y_poly = np.concatenate([y_out, y_in])

# 计算距离 y=x 的距离
dist_to_line = abs(cx_prime - cy_prime) / np.sqrt(2)
# 判断相交状态
# 环形区域与直线相交条件：距离 <= 外半径
# D'E'线段与直线相交条件：距离 在 [内半径, 外半径] 之间? 
# 准确说是：圆环与直线有交集。
intersect_status = "无交点"
status_color = "gray"
if dist_to_line > r_outer:
    intersect_status = "相离 (无解)"
    status_color = "red"
elif dist_to_line < r_inner:
    intersect_status = "包含直线 (可能无解，因为线段在两圆之间)" 
    # 注意：线段D'E'是连接内圆和外圆的弦。如果直线穿过内圆，线段必然会穿过直线。
    status_color = "orange"
else:
    intersect_status = "✅ 存在交点 (有解)"
    status_color = "green"

# 计算示例三角形
tri_points = get_triangle_CDE(c_val, angle_val, FIXED_N)
# 闭合用于画图
tri_plot = np.vstack([tri_points, tri_points[0]])

# --- 5. 绘图 ---
st.title("🎯 n型变换：D'E' 扫过区域探究")
st.markdown(f"""
**当前状态：** $n=3, c={c_val:.1f}$  
**中心点 $C'$ 坐标：** $({cx_prime:.1f}, {cy_prime:.1f})$  
**$C'$ 到 $y=x$ 距离：** ${dist_to_line:.3f}$ (范围参考: $[2, 2\sqrt{{2}}] \\approx [2, 2.828]$)  
**状态判定：** :{status_color}[**{intersect_status}**]
""")

fig = go.Figure()

# [图层0] y=x (黑色虚线)
fig.add_trace(go.Scatter(
    x=[-10, 20], y=[-10, 20], mode='lines', 
    line=dict(color='black', width=2, dash='dash'), name='y=x'
))

# [图层1] 扫过的圆环区域 (紫色半透明)
fig.add_trace(go.Scatter(
    x=x_poly, y=y_poly,
    fill='toself', 
    fillcolor='rgba(128, 0, 128, 0.2)', # 紫色半透明
    line=dict(color='rgba(0,0,0,0)'),   # 无边框
    name="D'E' 扫过区域",
    hoverinfo='skip'
))

# [图层2] 内圆 (D' 轨迹)
fig.add_trace(go.Scatter(
    x=x_in, y=y_in, mode='lines',
    line=dict(color='purple', width=1, dash='dot'),
    name="D' 轨迹圆 (r=2)"
))

# [图层3] 外圆 (E' 轨迹)
fig.add_trace(go.Scatter(
    x=x_out, y=y_out, mode='lines',
    line=dict(color='purple', width=2),
    name="E' 轨迹圆 (r=2√2)"
))

# [图层4] 中心点 C'
fig.add_trace(go.Scatter(
    x=[cx_prime], y=[cy_prime], mode='markers+text',
    marker=dict(size=10, color='red'),
    text=["<b>C'</b>"], textposition="middle center", textfont=dict(color='white'),
    name="中心 C'"
))

# [图层5] 示例三角形 (可选)
if show_sample_tri:
    # 填充三角形
    fig.add_trace(go.Scatter(
        x=tri_plot[:,0], y=tri_plot[:,1],
        mode='lines', fill='toself', fillcolor='rgba(0, 200, 100, 0.3)',
        line=dict(color='green', width=2),
        name="当前示例三角形"
    ))
    # D'E' 线段高亮
    fig.add_trace(go.Scatter(
        x=[tri_points[1,0], tri_points[2,0]], 
        y=[tri_points[1,1], tri_points[2,1]],
        mode='lines+markers+text',
        marker=dict(size=6, color='darkgreen'),
        line=dict(color='darkgreen', width=4),
        text=["<b>D'</b>", "<b>E'</b>"], textposition="top center", textfont=dict(size=14, color='darkgreen'),
        name="D'E' 线段"
    ))

# 布局设置 (保持白板风格)
fig.update_layout(
    paper_bgcolor='white', plot_bgcolor='white',
    height=700,
    xaxis=dict(
        range=[-2, 14], scaleratio=1, scaleanchor="y",
        zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
        title=dict(text="x", font=dict(color="black")),
        tickfont=dict(color="black")
    ),
    yaxis=dict(
        range=[-2, 10], 
        zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
        title=dict(text="y", font=dict(color="black")),
        tickfont=dict(color="black")
    ),
    legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.8)", font=dict(color="black"))
)

st.plotly_chart(fig, use_container_width=True)
