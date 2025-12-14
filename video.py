import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="n型变换：精准相交判定版",
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
    
    return np.array([[xc_prime, yc_prime], [D_prime_x, D_prime_y], [E_prime_x, E_prime_y]])

def get_valid_sector_shape(c_val):
    """
    计算有效扇环区域的边界坐标
    返回 x_coords, y_coords
    """
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    
    # 有效角度范围 [135, 270]
    # 增加采样密度以提高碰撞检测精度
    valid_angles = np.linspace(135, 270, 60)
    thetas = np.radians(valid_angles)
    
    # 内弧 (D') & 外弧 (E')
    d_x = xc_prime + 2 * np.cos(thetas)
    d_y = yc_prime - 2 * np.sin(thetas)
    e_x = xc_prime + (2 * np.cos(thetas) + 2 * np.sin(thetas))
    e_y = yc_prime + (2 * np.cos(thetas) - 2 * np.sin(thetas))
    
    # 拼接成闭合多边形 (外弧 -> 内弧反向 -> 闭合)
    poly_x = np.concatenate([e_x, d_x[::-1], [e_x[0]]])
    poly_y = np.concatenate([e_y, d_y[::-1], [e_y[0]]])
    
    return poly_x, poly_y

def check_polygon_line_intersection(poly_x, poly_y):
    """
    【核心修复】基于多边形边界的精确相交检测
    原理：直线 y=x 等价于 f(x,y) = x - y = 0
    我们检查多边形的每一条边，其两个端点 (x1, y1) 和 (x2, y2)
    如果 (x1-y1) 和 (x2-y2) 异号，说明这条边穿过了 y=x。
    """
    # 计算所有顶点相对于直线 y=x 的“符号距离” (x - y)
    diffs = poly_x - poly_y
    
    # 1. 快速排斥：如果所有点都在直线同一侧，肯定不相交
    if np.all(diffs > 1e-5) or np.all(diffs < -1e-5):
        return False
    
    # 2. 精确检测：遍历每一条边，看是否跨越 0
    has_crossing = False
    for i in range(len(diffs) - 1):
        # 如果两个相邻点在直线异侧 (乘积小于0)，说明有交点
        # 或者有点正好在直线上 (乘积等于0)
        if diffs[i] * diffs[i+1] <= 1e-6:
            has_crossing = True
            break
            
    return has_crossing

def get_circles_trace(c_val):
    """获取完整的轨迹圆虚线"""
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    full_rad = np.radians(np.linspace(0, 360, 90))
    
    # 内圆 r=2
    cin_x = xc_prime + 2 * np.cos(full_rad)
    cin_y = yc_prime + 2 * np.sin(full_rad)
    # 外圆 r=2sqrt(2)
    r_out = 2 * np.sqrt(2)
    cout_x = xc_prime + r_out * np.cos(full_rad)
    cout_y = yc_prime + r_out * np.sin(full_rad)
    
    return np.concatenate([cin_x, [None], cout_x]), np.concatenate([cin_y, [None], cout_y])

# --- 3. 动画帧生成 ---
c_start, c_end = -2.0, 6.0
steps = 100 
c_values = np.linspace(c_start, c_end, steps)
frames = []

for val in c_values:
    # 1. 计算形状
    sx, sy = get_valid_sector_shape(val)
    circ_x, circ_y = get_circles_trace(val)
    cx, cy = val + FIXED_N, 2 * FIXED_N - val
    tri = get_triangle_CDE(val, 180) 
    
    # 2. 【核心修复】精确判定
    is_intersect = check_polygon_line_intersection(sx, sy)
    
    if is_intersect:
        status_text = "✅ <b>相交</b>"
        status_color = "#008000" # 深绿
    else:
        status_text = "❌ 相离"
        status_color = "gray"
    
    frames.append(go.Frame(
        name=f"{val:.2f}",
        traces=[2, 3, 4, 5, 6],
        data=[
            # [2] 扇环
            go.Scatter(x=sx, y=sy),
            # [3] 完整圆轨迹
            go.Scatter(x=circ_x, y=circ_y),
            # [4] C'
            go.Scatter(x=[cx], y=[cy]),
            # [5] 示例三角形
            go.Scatter(
                x=np.vstack([tri, tri[0]])[:,0], 
                y=np.vstack([tri, tri[0]])[:,1],
                # textposition 已在 layout 固定，这里无需重复
            ),
            # [6] 状态文字
            go.Scatter(
                x=[cx + 2], y=[cy], 
                text=[f"<b>c={val:.1f}</b><br><span style='color:{status_color}; font-size:18px'>{status_text}</span>"],
            )
        ]
    ))

# 初始第一帧
init_c = c_values[0]
sx_0, sy_0 = get_valid_sector_shape(init_c)
circ_x0, circ_y0 = get_circles_trace(init_c)
cx_0, cy_0 = init_c + FIXED_N, 2 * FIXED_N - init_c
tri_0 = get_triangle_CDE(init_c, 180)
init_intersect = check_polygon_line_intersection(sx_0, sy_0)
init_status = "✅ <b>相交</b>" if init_intersect else "❌ 相离"
init_color = "#008000" if init_intersect else "gray"

# --- 4. 绘图主程序 ---
st.title("🎯 n型变换：精确碰撞检测演示")

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
            name="有效区域", hoverinfo='skip'
        ),
        
        # [3] 完整圆轨迹
        go.Scatter(
            x=circ_x0, y=circ_y0, mode='lines',
            line=dict(color='gray', width=1, dash='dot'),
            name="完整轨迹", hoverinfo='skip'
        ),
        
        # [4] C'点
        go.Scatter(
            x=[cx_0], y=[cy_0], mode='markers',
            marker=dict(size=8, color='red'), name="C'"
        ),
        
        # [5] 示例三角形
        go.Scatter(
            x=np.vstack([tri_0, tri_0[0]])[:,0],
            y=np.vstack([tri_0, tri_0[0]])[:,1],
            mode='lines+text',
            line=dict(color='green', width=2),
            text=["<b>C'</b>", "<b>D'</b>", "<b>E'</b>", ""], 
            textposition=["top right", "bottom left", "bottom right", "top right"],
            textfont=dict(color='black', size=14),
            name="示例 D'E'"
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

# 布局设置
fig.update_layout(
    paper_bgcolor='white', plot_bgcolor='white',
    font=dict(color='black', size=14),
    height=700,
    title=dict(text="<b>点击播放 ▶️ 观察紫色区域是否穿过虚线</b>", x=0.5, font=dict(color='black')),
    
    xaxis=dict(range=[-2, 14], scaleratio=1, scaleanchor="y", 
               zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
               tickfont=dict(color='black'), title=dict(text="x", font=dict(color='black'))),
    yaxis=dict(range=[-2, 10], 
               zeroline=True, zerolinecolor='black', gridcolor='#e0e0e0', showgrid=True,
               tickfont=dict(color='black'), title=dict(text="y", font=dict(color='black'))),
    
    # 动画设置 (速度调整为 60ms)
    updatemenus=[dict(
        type="buttons", showactive=False,
        x=0.1, y=0, xanchor="right", yanchor="top",
        bgcolor="white", bordercolor="black", borderwidth=1, font=dict(color="black"),
        buttons=[dict(
            label="▶️ 播放 (正常速度)",
            method="animate",
            # duration=60ms -> 既不拖沓，也能看清相交细节
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
