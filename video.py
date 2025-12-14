import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="n型变换：完美演示版",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 ---
FIXED_N = 3.0

def get_triangle_CDE(c, angle_deg):
    """计算变换后的示例三角形 C'D'E' (用于展示点的位置)"""
    theta = np.radians(angle_deg)
    xc_prime = c + FIXED_N
    yc_prime = 2 * FIXED_N - c
    
    # 相对向量计算
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
    
    # 返回 C', D', E' 三个点
    return np.array([[xc_prime, yc_prime], [D_prime_x, D_prime_y], [E_prime_x, E_prime_y]])

def get_sector_and_circles(c_val):
    """同时计算有效扇环和完整轨迹圆"""
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    
    # --- A. 有效扇环 (135度到270度) ---
    valid_angles = np.linspace(135, 270, 40)
    thetas = np.radians(valid_angles)
    
    d_x = xc_prime + 2 * np.cos(thetas)
    d_y = yc_prime - 2 * np.sin(thetas)
    e_x = xc_prime + (2*np.cos(thetas) + 2*np.sin(thetas))
    e_y = yc_prime + (2*np.cos(thetas) - 2*np.sin(thetas))
    
    sector_x = np.concatenate([e_x, d_x[::-1], [e_x[0]]])
    sector_y = np.concatenate([e_y, d_y[::-1], [e_y[0]]])
    
    # --- B. 完整轨迹圆 (0度到360度) ---
    full_angles = np.linspace(0, 360, 90)
    full_rad = np.radians(full_angles)
    
    circle_in_x = xc_prime + 2 * np.cos(full_rad)
    circle_in_y = yc_prime + 2 * np.sin(full_rad)
    
    r_out = 2 * np.sqrt(2)
    circle_out_x = xc_prime + r_out * np.cos(full_rad)
    circle_out_y = yc_prime + r_out * np.sin(full_rad)
    
    circles_x = np.concatenate([circle_in_x, [None], circle_out_x])
    circles_y = np.concatenate([circle_in_y, [None], circle_out_y])
    
    return sector_x, sector_y, circles_x, circles_y

def check_intersection_status(c_val):
    """相交判断逻辑"""
    cx = c_val + FIXED_N
    cy = 2 * FIXED_N - c_val
    dist = abs(cx - cy) / np.sqrt(2)
    r_in, r_out = 2.0, 2.0 * np.sqrt(2)
    
    if dist > r_out: return "❌ 相离", "gray"
    elif dist < r_in: return "⚠️ 包含无解", "orange"
    else: return "✅ **相交**", "#008000"

# --- 3. 动画帧生成 ---
c_start, c_end = -2.0, 6.0
steps = 100 
c_values = np.linspace(c_start, c_end, steps)
frames = []

for val in c_values:
    sx, sy, circ_x, circ_y = get_sector_and_circles(val)
    cx, cy = val + FIXED_N, 2 * FIXED_N - val
    tri = get_triangle_CDE(val, 180) 
    status_text, status_color = check_intersection_status(val)
    
    frames.append(go.Frame(
        name=f"{val:.2f}",
        traces=[2, 3, 4, 5, 6],
        data=[
            # [2] 有效扇环
            go.Scatter(x=sx, y=sy),
            # [3] 完整圆轨迹
            go.Scatter(x=circ_x, y=circ_y),
            # [4] C' 中心点
            go.Scatter(x=[cx], y=[cy]),
            # [5] 示例三角形 + 顶点字母
            go.Scatter(
                x=np.vstack([tri, tri[0]])[:,0], 
                y=np.vstack([tri, tri[0]])[:,1],
                text=["<b>C'</b>", "<b>D'</b>", "<b>E'</b>", ""],
                # 这里的 textposition 在 update 时不需要再次指定，会沿用 layout 或初始 trace 的设置
            ),
            # [6] 状态文字
            go.Scatter(
                x=[cx + 2], y=[cy], 
                text=[f"<b>c={val:.1f}</b><br><span style='color:{status_color}; font-size:16px'>{status_text}</span>"],
            )
        ]
    ))

# 初始第一帧数据
init_c = c_values[0]
sx_0, sy_0, circ_x0, circ_y0 = get_sector_and_circles(init_c)
cx_0, cy_0 = init_c + FIXED_N, 2 * FIXED_N - init_c
tri_0 = get_triangle_CDE(init_c, 180)
init_status, init_color = check_intersection_status(init_c)

# --- 4. 绘图主程序 ---
st.title("🎯 n型变换：区域扫描 (慢速演示版)")

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
        # [2] 有效扇环 (紫色)
        go.Scatter(
            x=sx_0, y=sy_0,
            fill='toself', fillcolor='rgba(128, 0, 128, 0.3)',
            line=dict(color='purple', width=1),
            name="有效区域", hoverinfo='skip'
        ),
        
        # [3] 完整圆轨迹 (灰色虚线)
        go.Scatter(
            x=circ_x0, y=circ_y0,
            mode='lines',
            line=dict(color='gray', width=1, dash='dot'),
            name="完整轨迹圆", hoverinfo='skip'
        ),
        
        # [4] C'点
        go.Scatter(
            x=[cx_0], y=[cy_0], mode='markers',
            marker=dict(size=8, color='red'), name="C'"
        ),
        
        # [5] 示例三角形 + 顶点字母 (已修复报错)
        go.Scatter(
            x=np.vstack([tri_0, tri_0[0]])[:,0],
            y=np.vstack([tri_0, tri_0[0]])[:,1],
            mode='lines+text',
            line=dict(color='green', width=2),
            text=["<b>C'</b>", "<b>D'</b>", "<b>E'</b>", ""], 
            # 【修复点】：第4个位置必须是有效字符串，不能是空字符串，即使它不显示文字
            textposition=["top right", "bottom left", "bottom right", "top right"], 
            textfont=dict(color='black', size=14),
            name="示例 D'E'"
        ),
        
        # [6] 状态标签
        go.Scatter(
            x=[cx_0 + 2], y=[cy_0], mode='text',
            text=[f"<b>c={init_c:.1f}</b><br><span style='color:{init_color}; font-size:16px'>{init_status}</span>"],
            textposition="middle right",
            textfont=dict(size=14, color='black'),
            showlegend=False
        )
    ],
    frames=frames
)

# 布局设置
fig.update_layout(
    paper_bgcolor='white', plot_bgcolor='white',
    font=dict(color='black', size=14),
    height=700,
    title=dict(text="<b>点击播放 ▶️ 观察相交 (已减速)</b>", x=0.5, font=dict(color='black')),
    
    xaxis=dict(range=[-2, 14], scaleratio=1, scaleanchor="y", 
               zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
               tickfont=dict(color='black'), title=dict(text="x", font=dict(color='black'))),
    yaxis=dict(range=[-2, 10], 
               zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
               tickfont=dict(color='black'), title=dict(text="y", font=dict(color='black'))),
    
    updatemenus=[dict(
        type="buttons", showactive=False,
        x=0.1, y=0, xanchor="right", yanchor="top",
        bgcolor="white", bordercolor="black", borderwidth=1, font=dict(color="black"),
        buttons=[dict(
            label="▶️ 播放 (慢速)",
            method="animate",
            args=[None, dict(frame=dict(duration=150, redraw=True), fromcurrent=True)]
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
