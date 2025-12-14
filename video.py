import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="n型变换：全功能终极版",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 ---
FIXED_N = 3.0

def get_triangle_CDE(c, angle_deg):
    """计算变换后的示例三角形 C'D'E'"""
    theta = np.radians(angle_deg)
    xc_prime = c + FIXED_N
    yc_prime = 2 * FIXED_N - c
    
    # 相对向量
    vec_CD_x = 2 * np.cos(theta)
    vec_CD_y = 2 * np.sin(theta)
    vec_DE_x = vec_CD_y
    vec_DE_y = -vec_CD_x
    vec_CE_x = vec_CD_x + vec_DE_x
    vec_CE_y = vec_CD_y + vec_DE_y
    
    # 绝对坐标
    D_prime_x = xc_prime + vec_CD_x
    D_prime_y = yc_prime - vec_CD_y 
    E_prime_x = xc_prime + vec_CE_x
    E_prime_y = yc_prime - vec_CE_y 
    
    return np.array([[xc_prime, yc_prime], [D_prime_x, D_prime_y], [E_prime_x, E_prime_y]])

def get_valid_sector_shape(c_val):
    """计算有效扇环区域 (紫色背景)"""
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    valid_angles = np.linspace(135, 270, 60)
    thetas = np.radians(valid_angles)
    
    d_x = xc_prime + 2 * np.cos(thetas)
    d_y = yc_prime - 2 * np.sin(thetas)
    e_x = xc_prime + (2*np.cos(thetas) + 2*np.sin(thetas))
    e_y = yc_prime + (2*np.cos(thetas) - 2*np.sin(thetas))
    
    poly_x = np.concatenate([e_x, d_x[::-1], [e_x[0]]])
    poly_y = np.concatenate([e_y, d_y[::-1], [e_y[0]]])
    return poly_x, poly_y

def get_circles_trace(c_val):
    """完整轨迹圆虚线"""
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    full_rad = np.radians(np.linspace(0, 360, 90))
    
    cin_x = xc_prime + 2 * np.cos(full_rad)
    cin_y = yc_prime + 2 * np.sin(full_rad)
    r_out = 2 * np.sqrt(2)
    cout_x = xc_prime + r_out * np.cos(full_rad)
    cout_y = yc_prime + r_out * np.sin(full_rad)
    
    return np.concatenate([cin_x, [None], cout_x]), np.concatenate([cin_y, [None], cout_y])

def check_angle_validity(angle):
    """
    判断当前角度是否符合 xD <= c 且 xE <= c
    理论范围: [135, 270]
    """
    # 稍微给一点浮点数容差
    if 135 - 0.1 <= angle <= 270 + 0.1:
        return True, "✅ 角度满足题意", "green"
    else:
        return False, "❌ 角度不合题意 (须 $135^\\circ \\le \\theta \\le 270^\\circ$)", "gray"

def check_polygon_line_intersection(poly_x, poly_y):
    """多边形与直线 y=x 相交检测"""
    diffs = poly_x - poly_y
    if np.all(diffs > 1e-5) or np.all(diffs < -1e-5): return False
    for i in range(len(diffs) - 1):
        if diffs[i] * diffs[i+1] <= 1e-6: return True
    return False

# --- 3. 侧边栏与交互 ---
with st.sidebar:
    st.header("🎮 控制台")
    st.markdown("### 1. 旋转自由度")
    angle_val = st.slider("📐 调整旋转角度 (θ)", 0, 360, 180, 5)
    
    is_angle_valid, angle_msg, angle_color = check_angle_validity(angle_val)
    if is_angle_valid:
        st.success(angle_msg)
    else:
        st.warning(angle_msg)

    st.divider()
    st.markdown("### 2. 平移自由度 (动画)")
    st.info("点击下方播放键控制 c")

# --- 4. 动画帧生成 ---
c_start, c_end = -2.0, 6.0
steps = 100
c_values = np.linspace(c_start, c_end, steps)
frames = []

for val in c_values:
    # 计算数据
    sx, sy = get_valid_sector_shape(val)
    circ_x, circ_y = get_circles_trace(val)
    cx, cy = val + FIXED_N, 2 * FIXED_N - val
    tri = get_triangle_CDE(val, angle_val) # 使用侧边栏选定的角度
    
    # 状态判定
    is_intersect = check_polygon_line_intersection(sx, sy)
    status_text = "✅ <b>扇环与直线相交</b>" if is_intersect else "❌ 相离"
    status_color = "#008000" if is_intersect else "gray"
    
    # 三角形颜色根据角度合法性改变
    tri_color = "green" if is_angle_valid else "gray"
    tri_opacity = 1.0 if is_angle_valid else 0.3
    
    frames.append(go.Frame(
        name=f"{val:.2f}",
        traces=[2, 3, 4, 5, 6],
        data=[
            # [2] 扇环
            go.Scatter(x=sx, y=sy),
            # [3] 轨迹圆
            go.Scatter(x=circ_x, y=circ_y),
            # [4] C'
            go.Scatter(x=[cx], y=[cy]),
            # [5] 示例三角形 (随角度变化颜色)
            go.Scatter(
                x=np.vstack([tri, tri[0]])[:,0], 
                y=np.vstack([tri, tri[0]])[:,1],
                line=dict(color=tri_color, width=2),
                opacity=tri_opacity
            ),
            # [6] 状态文字
            go.Scatter(
                x=[cx + 2], y=[cy], 
                text=[f"<b>c={val:.1f}</b><br><span style='color:{status_color}; font-size:18px'>{status_text}</span>"],
            )
        ]
    ))

# 初始帧计算
init_c = c_values[0]
sx_0, sy_0 = get_valid_sector_shape(init_c)
circ_x0, circ_y0 = get_circles_trace(init_c)
cx_0, cy_0 = init_c + FIXED_N, 2 * FIXED_N - init_c
tri_0 = get_triangle_CDE(init_c, angle_val)
init_intersect = check_polygon_line_intersection(sx_0, sy_0)
init_status = "✅ <b>扇环与直线相交</b>" if init_intersect else "❌ 相离"
init_color = "#008000" if init_intersect else "gray"
tri_color_0 = "green" if is_angle_valid else "gray"
tri_opacity_0 = 1.0 if is_angle_valid else 0.3

# --- 5. 绘图主程序 ---
st.title("🎯 n型变换：双自由度判定演示")

fig = go.Figure(
    data=[
        # --- 静态层 ---
        # [0] y=x
        go.Scatter(x=[-10, 20], y=[-10, 20], mode='lines', 
                   line=dict(color='black', width=2, dash='dash'), name='y=x', hoverinfo='skip'),
        # [1] y=3
        go.Scatter(x=[-10, 20], y=[3, 3], mode='lines', 
                   line=dict(color='blue', width=2, dash='dashdot'), name='y=3', hoverinfo='skip'),
        
        # --- 动态层 ---
        # [2] 有效扇环
        go.Scatter(
            x=sx_0, y=sy_0,
            fill='toself', fillcolor='rgba(128, 0, 128, 0.4)',
            line=dict(color='purple', width=1),
            name="符合题意区域", hoverinfo='skip'
        ),
        
        # [3] 完整圆轨迹
        go.Scatter(
            x=circ_x0, y=circ_y0, mode='lines',
            line=dict(color='gray', width=1, dash='dot'),
            name="完整轨迹圆", hoverinfo='skip'
        ),
        
        # [4] C'点
        go.Scatter(
            x=[cx_0], y=[cy_0], mode='markers',
            marker=dict(size=8, color='red'), name="C'"
        ),
        
        # [5] 示例三角形 (受角度控制)
        go.Scatter(
            x=np.vstack([tri_0, tri_0[0]])[:,0],
            y=np.vstack([tri_0, tri_0[0]])[:,1],
            mode='lines+text',
            line=dict(color=tri_color_0, width=2),
            opacity=tri_opacity_0,
            text=["<b>C'</b>", "<b>D'</b>", "<b>E'</b>", ""], 
            textposition=["top right", "bottom left", "bottom right", "top right"],
            textfont=dict(color='black', size=14),
            name="当前 D'E'"
        ),
        
        # [6] 状态标签
        go.Scatter(
            x=[cx_0 + 2], y=[cy_0], mode='text',
            text=[f"<b>c={init_c:.1f}</b><br><span style='color:{init_color}; font-size:18px'>{init_status}</span>"],
            textposition="middle right",
            textfont=dict(size=14, color='black'),
            showlegend=False
        )
    ],
    frames=frames
)

# 布局设置 (修复图例不清)
fig.update_layout(
    paper_bgcolor='white', plot_bgcolor='white',
    font=dict(color='black', size=14),
    height=700,
    title=dict(text="<b>手动调节角度 + 自动播放移动</b>", x=0.5, font=dict(color='black')),
    
    xaxis=dict(range=[-2, 14], scaleratio=1, scaleanchor="y", 
               zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
               tickfont=dict(color='black'), title=dict(text="x", font=dict(color='black'))),
    yaxis=dict(range=[-2, 10], 
               zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
               tickfont=dict(color='black'), title=dict(text="y", font=dict(color='black'))),
    
    # 【核心修复】图例清晰化
    legend=dict(
        x=0.01, y=0.99,
        bgcolor="rgba(255, 255, 255, 0.9)", # 半透明白底
        bordercolor="black", borderwidth=1,
        font=dict(color="black", size=12)   # 强制黑字
    ),
    
    updatemenus=[dict(
        type="buttons", showactive=False,
        x=0.1, y=0, xanchor="right", yanchor="top",
        bgcolor="white", bordercolor="black", borderwidth=1, font=dict(color="black"),
        buttons=[dict(
            label="▶️ 播放动画",
            method="animate",
            args=[None, dict(frame=dict(duration=60, redraw=True), fromcurrent=True)]
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
