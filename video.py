import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="n型变换(丝滑版)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心数学逻辑 ---
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
        t = progress / 0.5
        trans_points[:, 1] = points[:, 1] * (1 - t) + (2 * n - points[:, 1]) * t
    else:
        trans_points[:, 1] = 2 * n - points[:, 1]
        t = (progress - 0.5) / 0.5
        trans_points[:, 0] = points[:, 0] + t * n
    return trans_points

def check_intersection(points):
    D_prime = points[1]
    E_prime = points[2]
    val_D = D_prime[1] - D_prime[0]
    val_E = E_prime[1] - E_prime[0]
    return (val_D * val_E <= 0)

# --- 3. 侧边栏：只保留静态参数 ---
with st.sidebar:
    st.header("🎛️ 参数设置")
    st.info("💡 现在的动画在图表下方控制，点击 ▶️ 播放按钮体验极致丝滑。")
    
    # 这里的参数调整后，会重新生成整段动画
    c_val = st.slider("🅰️ 点 C 位置 (c)", -5.0, 8.0, 1.0, 0.1)
    n_val = st.slider("🅱️ 参数 n (对称轴 y=n)", 1.0, 5.0, 3.0, 0.1)
    angle_val = st.slider("🔄 旋转角度", 0, 360, 180, 5)

# --- 4. 生成动画帧 (核心黑科技) ---
# 我们一次性生成 0% 到 100% 的所有数据
frames = []
steps = 50 # 动画总帧数，越大越丝滑，但加载越慢。50-100 比较合适。
prog_values = np.linspace(0, 1, steps)

# 基础数据
pts_orig = get_triangle_CDE(c_val, angle_val)
plot_orig = np.vstack([pts_orig, pts_orig[0]]) # 闭合

for k, p in enumerate(prog_values):
    # 计算每一帧的形态
    pts_trans = apply_n_transform(pts_orig, n_val, p)
    plot_trans = np.vstack([pts_trans, pts_trans[0]])
    
    # 判断这一帧是否相交
    is_intersect = check_intersection(pts_trans)
    de_color = 'red' if is_intersect and p > 0.9 else 'green'
    de_width = 5 if is_intersect and p > 0.9 else 3
    
    # 创建帧对象
    frames.append(go.Frame(
        data=[
            # 更新[图层4]: 变换后三角形
            go.Scatter(x=plot_trans[:, 0], y=plot_trans[:, 1]), 
            # 更新[图层5]: D'E' 线段
            go.Scatter(
                x=[pts_trans[1,0], pts_trans[2,0]], 
                y=[pts_trans[1,1], pts_trans[2,1]],
                line=dict(color=de_color, width=de_width)
            )
        ],
        name=str(k) # 帧的名字
    ))

# --- 5. 主界面绘制 ---
st.title("🎬 n型变换：影院级丝滑演示")

# 初始状态 (进度=0)
pts_start = apply_n_transform(pts_orig, n_val, 0.0)
plot_start = np.vstack([pts_start, pts_start[0]])

fig = go.Figure(
    data=[
        # [0] y=x
        go.Scatter(x=[-10, 20], y=[-10, 20], mode='lines', line=dict(color='black', dash='dash'), name='y=x'),
        # [1] 对称轴
        go.Scatter(x=[-10, 20], y=[n_val, n_val], mode='lines', line=dict(color='blue', dash='dashdot'), name=f'y={n_val}'),
        # [2] 原三角形
        go.Scatter(x=plot_orig[:,0], y=plot_orig[:,1], mode='lines+markers+text', 
                   line=dict(color='purple', dash='dot'), text=["C","D","E",""], textfont=dict(size=16, color='purple'), name='原像'),
        # [3] C点指示
        go.Scatter(x=[c_val,c_val], y=[-10,20], mode='lines', line=dict(color='red', width=1, dash='dot'), showlegend=False),
        
        # --- 动态层 (需要被动画更新的) ---
        # [4] 变换后三角形 (初始状态)
        go.Scatter(
            x=plot_start[:,0], y=plot_start[:,1], 
            fill='toself', fillcolor='rgba(0, 200, 100, 0.3)',
            line=dict(color='green', width=3),
            mode='lines+markers+text', text=["<b>C'</b>","<b>D'</b>","<b>E'</b>",""], textfont=dict(size=16, color='black'),
            name='变换像'
        ),
        # [5] D'E' 高亮线段
        go.Scatter(x=[pts_start[1,0], pts_start[2,0]], y=[pts_start[1,1], pts_start[2,1]], mode='lines', line=dict(color='green', width=3), name="D'E'")
    ],
    frames=frames # 把预计算好的帧塞进去
)

# --- 6. 动画控件配置 ---
fig.update_layout(
    template="simple_white",
    height=700,
    title=dict(text="<b>几何变换动态演示系统</b>", font=dict(size=22), x=0.5),
    xaxis=dict(range=[-6, 15], scaleanchor="y", scaleratio=1),
    yaxis=dict(range=[-6, 12]),
    
    # 动画按钮设置
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        x=0.1, y=0, xanchor="right", yanchor="top", # 按钮位置
        pad=dict(t=0, r=10),
        buttons=[dict(
            label="▶️ 播放",
            method="animate",
            args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True, transition=dict(duration=0))]
        ),
        dict(
            label="⏸️ 暂停",
            method="animate",
            args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
        )]
    )],
    
    # 底部滑块设置
    sliders=[dict(
        steps=[dict(
            method="animate",
            args=[[str(k)], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))],
            label=f"{p:.2f}"
        ) for k, p in enumerate(prog_values)],
        active=0,
        y=0, x=0.1, # 滑块位置
        len=0.9,    # 滑块长度
        pad=dict(t=0),
    )]
)

st.plotly_chart(fig, use_container_width=True)
