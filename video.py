import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="n型变换：双像对照演示",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 ---
FIXED_N = 3.0

def get_geometry_data(c, angle_deg):
    """
    计算两组三角形的数据：
    1. 原像 CDE (顺时针)
    2. 变换像 C'D'E' (n型变换后，自然变为逆时针)
    """
    theta = np.radians(angle_deg)
    
    # --- A. 计算原像 CDE ---
    # C 坐标
    Cx, Cy = c, c
    
    # D 坐标 (相对C)
    vec_CD_x = 2 * np.cos(theta)
    vec_CD_y = 2 * np.sin(theta)
    Dx = Cx + vec_CD_x
    Dy = Cy + vec_CD_y
    
    # E 坐标 (顺时针排列 => DE 是 CD 顺时针转90度)
    # 顺时针转90度: (x, y) -> (y, -x)
    vec_DE_x = vec_CD_y
    vec_DE_y = -vec_CD_x
    
    Ex = Dx + vec_DE_x
    Ey = Dy + vec_DE_y
    
    # 闭合用于画图
    orig_tri = np.array([[Cx, Cy], [Dx, Dy], [Ex, Ey], [Cx, Cy]])
    
    # --- B. 计算变换像 C'D'E' ---
    # n型变换: x' = x + n, y' = 2n - y
    def n_transform(x, y, n):
        return x + n, 2*n - y
    
    C_prime = n_transform(Cx, Cy, FIXED_N)
    D_prime = n_transform(Dx, Dy, FIXED_N)
    E_prime = n_transform(Ex, Ey, FIXED_N)
    
    trans_tri = np.array([C_prime, D_prime, E_prime, C_prime])
    
    return orig_tri, trans_tri

def get_valid_sector_shape(c_val):
    """
    计算变换后的有效扇环区域
    条件: xD <= c 且 xE <= c
    推导: theta in [135, 270] (基于原像顺时针推导)
    """
    valid_angles = np.linspace(135, 270, 50)
    thetas = np.radians(valid_angles)
    
    # 变换基准点 C'
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    
    # 注意：这里直接用变换后的向量公式来生成轨迹
    # 原像中: xD = c + 2cos, yD = c + 2sin
    # 变换后: xD' = (c + 2cos) + n = xc' + 2cos
    #        yD' = 2n - (c + 2sin) = (2n - c) - 2sin = yc' - 2sin
    
    # D' 轨迹 (内弧)
    d_x = xc_prime + 2 * np.cos(thetas)
    d_y = yc_prime - 2 * np.sin(thetas)
    
    # E' 轨迹 (外弧)
    # 原像中: xE = c + 2cos + 2sin
    # 变换后: xE' = xE + n = xc' + (2cos + 2sin)
    #        yE' = 2n - yE = yc' - (2sin - 2cos) = yc' - 2sin + 2cos
    e_x = xc_prime + (2 * np.cos(thetas) + 2 * np.sin(thetas))
    e_y = yc_prime - (2 * np.sin(thetas) - 2 * np.cos(thetas))
    
    # 闭合多边形
    poly_x = np.concatenate([e_x, d_x[::-1], [e_x[0]]])
    poly_y = np.concatenate([e_y, d_y[::-1], [e_y[0]]])
    
    return poly_x, poly_y

def get_circles_trace(c_val):
    """完整轨迹圆虚线 (基于变换后的 C')"""
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    full_rad = np.radians(np.linspace(0, 360, 90))
    
    # D' 轨迹圆
    cin_x = xc_prime + 2 * np.cos(full_rad)
    cin_y = yc_prime + 2 * np.sin(full_rad) # 画圆不需要管正负方向，形状是一样的
    
    # E' 轨迹圆
    r_out = 2 * np.sqrt(2)
    cout_x = xc_prime + r_out * np.cos(full_rad)
    cout_y = yc_prime + r_out * np.sin(full_rad)
    
    return np.concatenate([cin_x, [None], cout_x]), np.concatenate([cin_y, [None], cout_y])

def check_polygon_line_intersection(poly_x, poly_y):
    """检测多边形是否穿过 y=x"""
    diffs = poly_x - poly_y
    # 快速排斥
    if np.all(diffs > 1e-5) or np.all(diffs < -1e-5): return False
    # 跨越检测
    for i in range(len(diffs) - 1):
        if diffs[i] * diffs[i+1] <= 1e-6: return True
    return False

def check_angle_validity(angle):
    """
    判断当前角度是否符合题意
    范围: [135, 270]
    """
    norm_angle = angle % 360
    if 135 - 0.1 <= norm_angle <= 270 + 0.1:
        return True, "✅ 角度满足题意", "green"
    else:
        return False, "❌ 角度不合题意", "gray"

# --- 3. 侧边栏 ---
with st.sidebar:
    st.header("🎮 控制台")
    st.markdown("### 1. 旋转原像 (调整 θ)")
    angle_val = st.slider("📐 旋转角度", 0, 360, 180, 5)
    
    is_angle_valid, angle_msg, angle_color = check_angle_validity(angle_val)
    if is_angle_valid:
        st.success(angle_msg)
    else:
        st.error(angle_msg)

    st.divider()
    st.info("点击图表下方播放键，观察 c 的移动")

# --- 4. 动画帧生成 ---
c_start, c_end = -2.0, 6.0
steps = 100
c_values = np.linspace(c_start, c_end, steps)
frames = []

for val in c_values:
    # 1. 计算几何数据
    orig, trans = get_geometry_data(val, angle_val)
    sx, sy = get_valid_sector_shape(val)
    circ_x, circ_y = get_circles_trace(val)
    
    # 中心点
    cx, cy = val, val
    cx_p, cy_p = val + FIXED_N, 2 * FIXED_N - val
    
    # 2. 状态判定
    is_intersect = check_polygon_line_intersection(sx, sy)
    status_text = "✅ <b>相交</b>" if is_intersect else "❌ 相离"
    status_color = "#008000" if is_intersect else "gray"
    
    # 三角形样式
    tri_color = "green" if is_angle_valid else "gray"
    tri_opacity = 1.0 if is_angle_valid else 0.3
    
    frames.append(go.Frame(
        name=f"{val:.2f}",
        traces=[2, 3, 4, 5, 6, 7, 8], # 更新动态层
        data=[
            # [2] 扇环
            go.Scatter(x=sx, y=sy),
            # [3] 轨迹圆
            go.Scatter(x=circ_x, y=circ_y),
            # [4] 原像 CDE
            go.Scatter(x=orig[:,0], y=orig[:,1]),
            # [5] 变换像 C'D'E'
            go.Scatter(x=trans[:,0], y=trans[:,1], line=dict(color=tri_color), opacity=tri_opacity),
            # [6] C 点
            go.Scatter(x=[cx], y=[cy]),
            # [7] C' 点
            go.Scatter(x=[cx_p], y=[cy_p]),
            # [8] 状态文字
            go.Scatter(
                x=[cx_p + 1.5], y=[cy_p],
                text=[f"<b>c={val:.1f}</b><br><span style='color:{status_color}; font-size:18px'>{status_text}</span>"]
            )
        ]
    ))

# 初始计算
init_c = c_values[0]
orig_0, trans_0 = get_geometry_data(init_c, angle_val)
sx_0, sy_0 = get_valid_sector_shape(init_c)
circ_x0, circ_y0 = get_circles_trace(init_c)
is_intersect_0 = check_polygon_line_intersection(sx_0, sy_0)
init_status = "✅ <b>相交</b>" if is_intersect_0 else "❌ 相离"
init_color = "#008000" if is_intersect_0 else "gray"
tri_color_0 = "green" if is_angle_valid else "gray"
tri_opacity_0 = 1.0 if is_angle_valid else 0.3

# --- 5. 绘图主程序 ---
st.title("🎯 n型变换：双像对照与区域扫描")

fig = go.Figure(
    data=[
        # --- 静态背景层 (Index 0, 1) ---
        go.Scatter(x=[-10, 20], y=[-10, 20], mode='lines', 
                   line=dict(color='black', width=2, dash='dash'), name='y=x', hoverinfo='skip'),
        go.Scatter(x=[-10, 20], y=[3, 3], mode='lines', 
                   line=dict(color='blue', width=2, dash='dashdot'), name='y=3 (对称轴)', hoverinfo='skip'),
        
        # --- 动态层 (Index 2-8) ---
        # [2] 有效扇环 (紫色)
        go.Scatter(
            x=sx_0, y=sy_0,
            fill='toself', fillcolor='rgba(128, 0, 128, 0.3)',
            line=dict(color='purple', width=1),
            name="扫过区域 (C'D'E')", hoverinfo='skip'
        ),
        
        # [3] 完整轨迹圆 (灰色虚线)
        go.Scatter(
            x=circ_x0, y=circ_y0, mode='lines',
            line=dict(color='gray', width=1, dash='dot'),
            name="完整轨迹圆", hoverinfo='skip'
        ),
        
        # [4] 原像 CDE (紫色虚线)
        go.Scatter(
            x=orig_0[:,0], y=orig_0[:,1],
            mode='lines+text',
            line=dict(color='purple', width=2, dash='dot'),
            text=["<b>C</b>", "<b>D</b>", "<b>E</b>", ""],
            textposition=["top left", "top left", "bottom right", "top left"],
            textfont=dict(color='purple', size=14),
            name="原像 CDE (顺时针)"
        ),
        
        # [5] 变换像 C'D'E' (绿色实线)
        go.Scatter(
            x=trans_0[:,0], y=trans_0[:,1],
            mode='lines+text',
            line=dict(color=tri_color_0, width=2),
            opacity=tri_opacity_0,
            text=["<b>C'</b>", "<b>D'</b>", "<b>E'</b>", ""],
            textposition=["top right", "bottom left", "bottom right", "top right"],
            textfont=dict(color='black', size=14),
            name="变换像 C'D'E' (逆时针)"
        ),
        
        # [6] C点 (紫点)
        go.Scatter(
            x=[init_c], y=[init_c], mode='markers',
            marker=dict(size=6, color='purple'), name="C"
        ),
        
        # [7] C'点 (红点)
        go.Scatter(
            x=[init_c + FIXED_N], y=[2*FIXED_N - init_c], mode='markers',
            marker=dict(size=8, color='red'), name="C'"
        ),
        
        # [8] 状态文字
        go.Scatter(
            x=[init_c + FIXED_N + 1.5], y=[2*FIXED_N - init_c], mode='text',
            text=[f"<b>c={init_c:.1f}</b><br><span style='color:{init_color}; font-size:18px'>{init_status}</span>"],
            textposition="middle right",
            textfont=dict(size=14, color='black'),
            showlegend=False
        )
    ],
    frames=frames
)

fig.update_layout(
    paper_bgcolor='white', plot_bgcolor='white',
    font=dict(color='black', size=14),
    height=750,
    title=dict(text="<b>原像(虚线) vs 变换像(实线)</b>", x=0.5, font=dict(color='black')),
    
    xaxis=dict(range=[-4, 14], scaleratio=1, scaleanchor="y", 
               zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
               tickfont=dict(color='black'), title=dict(text="x", font=dict(color='black'))),
    yaxis=dict(range=[-4, 12], 
               zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
               tickfont=dict(color='black'), title=dict(text="y", font=dict(color='black'))),
    
    legend=dict(
        x=0.01, y=0.99,
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="black", borderwidth=1,
        font=dict(color="black", size=12)
    ),
    
    updatemenus=[dict(
        type="buttons", showactive=False,
        x=0.1, y=0, xanchor="right", yanchor="top",
        bgcolor="white", bordercolor="black", borderwidth=1, font=dict(color="black"),
        buttons=[dict(
            label="▶️ 播放动画",
            method="animate",
            args=[None, dict(frame=dict(duration=80, redraw=True), fromcurrent=True)]
        )]
    )],
    
    sliders=[dict(
        steps=[dict(
            method="animate",
            args=[[f"{v:.2f}"], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
            label=f"{v:.1f}"
        ) for v in c_values],
        currentvalue=dict(prefix="c = ", font=dict(color="black")),
        active=0,
        bgcolor="white", bordercolor="lightgray", borderwidth=1, font=dict(color="black")
    )]
)

st.plotly_chart(fig, use_container_width=True)
