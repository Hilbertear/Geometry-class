import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="n型变换：最终演示版",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 ---
FIXED_N = 3.0

def get_triangle_CDE(c, angle_deg):
    """计算变换后的三角形 C'D'E' 坐标"""
    theta = np.radians(angle_deg)
    
    # C' 坐标
    xc_prime = c + FIXED_N
    yc_prime = 2 * FIXED_N - c
    
    # 向量计算 (保持之前的逻辑)
    vec_CD_x = 2 * np.cos(theta)
    vec_CD_y = 2 * np.sin(theta)
    vec_DE_x = vec_CD_y
    vec_DE_y = -vec_CD_x
    vec_CE_x = vec_CD_x + vec_DE_x
    vec_CE_y = vec_CD_y + vec_DE_y
    
    # 变换后的 D' E'
    D_prime_x = xc_prime + vec_CD_x
    D_prime_y = yc_prime - vec_CD_y 
    E_prime_x = xc_prime + vec_CE_x
    E_prime_y = yc_prime - vec_CE_y 
    
    return np.array([[xc_prime, yc_prime], [D_prime_x, D_prime_y], [E_prime_x, E_prime_y]])

def get_valid_sector_shape(c_val):
    """计算有效扇环区域"""
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    valid_angles = np.linspace(135, 270, 40) # 降低采样点以提高动画性能
    thetas = np.radians(valid_angles)
    
    d_x = xc_prime + 2 * np.cos(thetas)
    d_y = yc_prime - 2 * np.sin(thetas)
    e_x = xc_prime + (2 * np.cos(thetas) + 2 * np.sin(thetas))
    e_y = yc_prime + (2 * np.cos(thetas) - 2 * np.sin(thetas))
    
    poly_x = np.concatenate([e_x, d_x[::-1], [e_x[0]]])
    poly_y = np.concatenate([e_y, d_y[::-1], [e_y[0]]])
    return poly_x, poly_y

def check_intersection_status(c_val):
    """
    判断扇环是否与 y=x 相交
    判据：C'到直线的距离 d。
    内半径 r=2, 外半径 R=2sqrt(2) approx 2.828
    当 2 <= d <= 2.828 时相交。
    C'(c+3, 6-c) 到 x-y=0 的距离:
    d = |(c+3) - (6-c)| / sqrt(2) = |2c - 3| / 1.414
    """
    cx = c_val + FIXED_N
    cy = 2 * FIXED_N - c_val
    dist = abs(cx - cy) / np.sqrt(2)
    
    r_in = 2.0
    r_out = 2.0 * np.sqrt(2)
    
    if dist > r_out:
        return "❌ 相离", "gray"
    elif dist < r_in:
        # 此时直线穿过内圆，扇环在直线两侧，虽然包含直线但没有交点（空心部分）
        # 不过题目通常指区域是否有公共点。如果是空心扇环，此时确实不相交。
        return "⚠️ 包含但无交点", "orange"
    else:
        return "✅ **发生相交**", "green" # 加粗提示

# --- 3. 动画帧生成 ---
c_start, c_end = -2.0, 6.0
steps = 60 # 帧数
c_values = np.linspace(c_start, c_end, steps)
frames = []

for val in c_values:
    # 1. 计算当前位置数据
    sx, sy = get_valid_sector_shape(val)
    cx = val + FIXED_N
    cy = 2 * FIXED_N - val
    demo_tri = get_triangle_CDE(val, 180) 
    status_text, status_color = check_intersection_status(val)
    
    # 2. 生成帧
    # 注意：这里的 traces=[2, 3, 4, 5] 是修复线条消失的关键！
    # 它告诉 Plotly：这一帧只更新第 2,3,4,5 个图层，不要动第 0,1 个图层(静态线)
    frames.append(go.Frame(
        name=f"{val:.2f}",
        traces=[2, 3, 4, 5], 
        data=[
            # [2] 扇环
            go.Scatter(x=sx, y=sy),
            # [3] C'点
            go.Scatter(x=[cx], y=[cy]),
            # [4] 示例三角形
            go.Scatter(x=np.vstack([demo_tri, demo_tri[0]])[:,0], y=np.vstack([demo_tri, demo_tri[0]])[:,1]),
            # [5] 动态文字标签 (c值 + 状态)
            go.Scatter(
                x=[cx + 1], y=[cy], # 文字稍微偏右一点，防止挡住点
                text=[f"<b>c={val:.1f}</b><br><span style='color:{status_color}; font-size:16px'>{status_text}</span>"],
                textfont=dict(color='black') # 强制每一帧文字都为黑
            )
        ]
    ))

# 初始数据 (第一帧)
init_c = c_values[0]
sx_0, sy_0 = get_valid_sector_shape(init_c)
cx_0 = init_c + FIXED_N
cy_0 = 2 * FIXED_N - init_c
tri_0 = get_triangle_CDE(init_c, 180)
init_status, init_color = check_intersection_status(init_c)

# --- 4. 绘图主程序 ---
st.title("🎯 n型变换：区域扫描与相交判定")

# 理论计算
st.markdown(r"**💡 观察提示：** 扇环区域（紫色）随着 $c$ 沿直线移动，当它接触到虚线 $y=x$ 时，即为满足题意的时刻。")

fig = go.Figure(
    data=[
        # --- 静态图层 (Index 0, 1) ---
        # 即使动画播放，这两个也不会动，也不会消失，因为 frames 里不更新它们
        
        # [0] y=x (黑色虚线，加粗)
        go.Scatter(x=[-10, 20], y=[-10, 20], mode='lines', 
                   line=dict(color='black', width=2, dash='dash'), 
                   name='y=x', hoverinfo='skip'),
                   
        # [1] y=3 (蓝色点划线，加粗)
        go.Scatter(x=[-10, 20], y=[3, 3], mode='lines', 
                   line=dict(color='blue', width=2, dash='dashdot'), 
                   name='y=3', hoverinfo='skip'),
        
        # --- 动态图层 (Index 2, 3, 4, 5) ---
        
        # [2] 有效扇环区域
        go.Scatter(
            x=sx_0, y=sy_0,
            fill='toself', fillcolor='rgba(128, 0, 128, 0.4)', # 紫色半透明，加深一点
            line=dict(color='purple', width=1),
            name="扫过区域", hoverinfo='skip'
        ),
        
        # [3] 中心点 C'
        go.Scatter(
            x=[cx_0], y=[cy_0], mode='markers',
            marker=dict(size=10, color='red', line=dict(color='black', width=1)),
            name="C'"
        ),
        
        # [4] 示例三角形
        go.Scatter(
            x=np.vstack([tri_0, tri_0[0]])[:,0],
            y=np.vstack([tri_0, tri_0[0]])[:,1],
            mode='lines', line=dict(color='green', width=2),
            name="示例三角形"
        ),
        
        # [5] 动态状态标签 (重点修复：颜色和可见性)
        go.Scatter(
            x=[cx_0 + 1], y=[cy_0], mode='text',
            text=[f"<b>c={init_c:.1f}</b><br><span style='color:{init_color}; font-size:16px'>{init_status}</span>"],
            textposition="middle right",
            textfont=dict(size=14, color='black'), # 强制黑色，防止变浅
            showlegend=False
        )
    ],
    frames=frames
)

# 布局设置 (强制白板风格，修复文字看不清的问题)
fig.update_layout(
    # 强制背景纯白
    paper_bgcolor='white', 
    plot_bgcolor='white',
    
    # 强制全局字体为黑色
    font=dict(color='black', size=14),
    
    height=700,
    title=dict(text="<b>点击下方播放键 ▶️ 开始扫描</b>", x=0.5, font=dict(color='black')),
    
    xaxis=dict(
        range=[-2, 14], scaleratio=1, scaleanchor="y",
        zeroline=True, zerolinecolor='black', zerolinewidth=2, # 坐标轴加黑
        gridcolor='#e0e0e0', showgrid=True,
        tickfont=dict(color='black'), # 刻度文字加黑
        title=dict(text="x", font=dict(color='black'))
    ),
    yaxis=dict(
        range=[-2, 10], 
        zeroline=True, zerolinecolor='black', zerolinewidth=2,
        gridcolor='#e0e0e0', showgrid=True,
        tickfont=dict(color='black'),
        title=dict(text="y", font=dict(color='black'))
    ),
    
    # 动画控件样式
    updatemenus=[dict(
        type="buttons", showactive=False,
        x=0.1, y=0, xanchor="right", yanchor="top",
        bgcolor="white", bordercolor="black", borderwidth=1, 
        font=dict(color="black"), # 按钮文字黑
        buttons=[dict(
            label="▶️ 播放动画",
            method="animate",
            args=[None, dict(frame=dict(duration=20, redraw=True), fromcurrent=True)]
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
        bgcolor="white", bordercolor="lightgray", borderwidth=1, 
        font=dict(color="black") # 滑块文字黑
    )]
)

st.plotly_chart(fig, use_container_width=True)
