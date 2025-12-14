import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="n型变换：受限区域探究",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 ---
FIXED_N = 3.0

def get_triangle_CDE(c, angle_deg):
    """
    计算变换后的三角形 C'D'E' 坐标
    """
    theta = np.radians(angle_deg)
    
    # 1. C' 的坐标 (变换后)
    # n型变换公式: x' = x+n, y' = 2n-y
    # C(c,c) -> C'(c+n, 2n-c)
    xc_prime = c + FIXED_N
    yc_prime = 2 * FIXED_N - c
    
    # 2. 计算相对位移 (向量)
    # 原像中: xD = c + 2cos(theta), yD = c + 2sin(theta)
    # 变换后: xD' = xD + n = c + n + 2cos(theta)
    #        yD' = 2n - yD = 2n - (c + 2sin(theta)) = (2n-c) - 2sin(theta)
    # 所以 D' 相对于 C' 的偏移量是 (2cos(theta), -2sin(theta))
    # 这相当于原向量在y方向取反，或者说是顺时针翻转了
    
    # 原始向量 (相对C)
    vec_CD_x = 2 * np.cos(theta)
    vec_CD_y = 2 * np.sin(theta)
    
    # 题目中 CD=DE=2, CD垂直DE, C,D,E顺时针
    # E相对于D的向量，是CD向量顺时针旋转90度
    # 旋转 -90度: x' = y, y' = -x
    vec_DE_x = vec_CD_y
    vec_DE_y = -vec_CD_x
    
    # E 相对于 C 的向量 = CD + DE
    vec_CE_x = vec_CD_x + vec_DE_x
    vec_CE_y = vec_CD_y + vec_DE_y
    
    # 3. 应用变换 (翻折+平移) 到相对向量上
    # 变换规律：x方向不变，y方向取反 (因为 y' = 2n - y，线性部分斜率为-1)
    
    # D' 绝对坐标
    D_prime_x = xc_prime + vec_CD_x
    D_prime_y = yc_prime - vec_CD_y # 注意这里减号，体现翻折
    
    # E' 绝对坐标
    E_prime_x = xc_prime + vec_CE_x
    E_prime_y = yc_prime - vec_CE_y # 注意这里减号
    
    return np.array([[xc_prime, yc_prime], [D_prime_x, D_prime_y], [E_prime_x, E_prime_y]])

def get_valid_sector_shape(c_val):
    """
    计算满足条件 xD <= c 且 xE <= c 的扇环区域形状
    数学推导：
    xD <= c => 2cos(theta) <= 0 => theta in [90, 270]
    xE <= c => xD + 2sin(theta) <= c => 2cos+2sin <= 0 => sin(theta+45)<=0 => theta in [135, 315]
    交集: theta in [135, 270]
    """
    xc_prime = c_val + FIXED_N
    yc_prime = 2 * FIXED_N - c_val
    
    # 有效角度范围 (原像角度)
    valid_angles = np.linspace(135, 270, 50)
    thetas = np.radians(valid_angles)
    
    # 构造 D' 的轨迹 (内弧)
    # D'x = xc' + 2cos(theta)
    # D'y = yc' - 2sin(theta)
    d_x = xc_prime + 2 * np.cos(thetas)
    d_y = yc_prime - 2 * np.sin(thetas)
    
    # 构造 E' 的轨迹 (外弧)
    # Ex_orig = 2cos + 2sin
    # Ey_orig = 2sin - 2cos
    # E'x = xc' + (2cos + 2sin)
    # E'y = yc' - (2sin - 2cos) = yc' + 2cos - 2sin
    e_x = xc_prime + (2 * np.cos(thetas) + 2 * np.sin(thetas))
    e_y = yc_prime + (2 * np.cos(thetas) - 2 * np.sin(thetas))
    
    # 拼接成闭合多边形: E'正向 -> D'反向 -> 回到起点
    poly_x = np.concatenate([e_x, d_x[::-1], [e_x[0]]])
    poly_y = np.concatenate([e_y, d_y[::-1], [e_y[0]]])
    
    return poly_x, poly_y

# --- 3. 动画帧生成 ---
c_start, c_end = -2.0, 6.0
steps = 80
c_values = np.linspace(c_start, c_end, steps)
frames = []

for val in c_values:
    # 1. 计算当前位置的扇环
    sx, sy = get_valid_sector_shape(val)
    
    # 2. 计算当前位置的 C'
    cx = val + FIXED_N
    cy = 2 * FIXED_N - val
    
    # 3. 计算示例三角形 (用于演示一个具体的 D'E')
    # 选一个在有效范围内的角度，比如 180度
    demo_tri = get_triangle_CDE(val, 180) 
    
    frames.append(go.Frame(
        name=f"{val:.2f}",
        data=[
            # [2] 扇环区域更新
            go.Scatter(x=sx, y=sy),
            # [3] C' 更新
            go.Scatter(x=[cx], y=[cy]),
            # [4] 示例三角形更新
            go.Scatter(x=np.vstack([demo_tri, demo_tri[0]])[:,0], 
                       y=np.vstack([demo_tri, demo_tri[0]])[:,1]),
            # [5] c值标签更新
            go.Scatter(x=[cx], text=[f"c={val:.1f}"])
        ]
    ))

# 初始数据 (第一帧)
init_c = c_values[0]
sx_0, sy_0 = get_valid_sector_shape(init_c)
cx_0 = init_c + FIXED_N
cy_0 = 2 * FIXED_N - init_c
tri_0 = get_triangle_CDE(init_c, 180)

# --- 4. 绘图主程序 ---
st.title("🎯 n型变换：受限区域与动态扫描")

# 数学原理解析
with st.expander("查看区域限制的数学推导"):
    st.latex(r"\text{由 } x_D \le c \implies 2\cos\theta \le 0 \implies 90^\circ \le \theta \le 270^\circ")
    st.latex(r"\text{由 } x_E \le c \implies 2\cos\theta + 2\sin\theta \le 0 \implies 135^\circ \le \theta \le 315^\circ")
    st.latex(r"\text{取交集：} \theta \in [135^\circ, 270^\circ]")
    st.write("图中 **紫色扇环** 即为该角度范围对应的 $D'E'$ 扫掠区域。")

fig = go.Figure(
    data=[
        # --- 静态背景层 ---
        # [0] y=x
        go.Scatter(x=[-10, 20], y=[-10, 20], mode='lines', 
                   line=dict(color='black', width=1.5, dash='dash'), name='y=x'),
        # [1] y=3 (n=3)
        go.Scatter(x=[-10, 20], y=[3, 3], mode='lines', 
                   line=dict(color='blue', width=2, dash='dashdot'), name='y=3 (对称轴)'),
        
        # --- 动态层 (需在 frames 中更新) ---
        # [2] 有效扇环区域
        go.Scatter(
            x=sx_0, y=sy_0,
            fill='toself', fillcolor='rgba(128, 0, 128, 0.3)', # 紫色半透明
            line=dict(color='purple', width=1),
            name="符合题意的区域"
        ),
        
        # [3] 中心点 C'
        go.Scatter(
            x=[cx_0], y=[cy_0], mode='markers',
            marker=dict(size=8, color='red'),
            name="C'"
        ),
        
        # [4] 示例三角形 (取 theta=180度)
        go.Scatter(
            x=np.vstack([tri_0, tri_0[0]])[:,0],
            y=np.vstack([tri_0, tri_0[0]])[:,1],
            mode='lines', line=dict(color='green', width=2),
            name="示例 D'E' (θ=180°)"
        ),
        
        # [5] c值文字标签
        go.Scatter(
            x=[cx_0], y=[cy_0 - 0.8], mode='text',
            text=[f"c={init_c:.1f}"], textfont=dict(color='red', size=14),
            showlegend=False
        )
    ],
    frames=frames
)

# 布局设置 (白板风格)
fig.update_layout(
    # 背景与字体
    paper_bgcolor='white', plot_bgcolor='white',
    font=dict(color='black'),
    
    height=700,
    title=dict(text="<b>点击下方播放键 ▶️ 观察扇环移动与相交</b>", x=0.5),
    
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
    
    # 动画控件
    updatemenus=[dict(
        type="buttons", showactive=False,
        x=0.1, y=0, xanchor="right", yanchor="top",
        bgcolor="white", bordercolor="black", borderwidth=1, font=dict(color="black"),
        buttons=[dict(
            label="▶️ 播放连续动画",
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
        bgcolor="white", bordercolor="lightgray", borderwidth=1, font=dict(color="black")
    )]
)

st.plotly_chart(fig, use_container_width=True)
