import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="几何变换全能演示(最终修复版)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 强制注入 CSS 样式 (解决背景不是白色的问题) ---
st.markdown("""
    <style>
    /* 强制背景变白 */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    /* 强制侧边栏背景变浅灰，以示区分 */
    section[data-testid="stSidebar"] {
        background-color: #f5f5f5;
        color: #000000;
    }
    /* 强制所有文字变黑 */
    h1, h2, h3, p, div, span, label {
        color: #000000 !important;
    }
    /* 修复滑块文字颜色 */
    .stSlider label {
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# PART A: 数学核心逻辑
# ==========================================
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
        # 翻折阶段
        t = progress / 0.5
        trans_points[:, 1] = points[:, 1] * (1 - t) + (2 * n - points[:, 1]) * t
    else:
        # 平移阶段
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

def calc_c_range(angle_deg, n):
    base_tri = get_triangle_CDE(0, angle_deg)
    sum_D = base_tri[1, 0] + base_tri[1, 1]
    sum_E = base_tri[2, 0] + base_tri[2, 1]
    c1 = (n - sum_D) / 2
    c2 = (n - sum_E) / 2
    return min(c1, c2), max(c1, c2)

# ==========================================
# PART B: 通用绘图数据生成器
# ==========================================
def get_trace_data(c, n, angle, progress):
    # 1. 计算
    pts_orig = get_triangle_CDE(c, angle)
    pts_trans = apply_n_transform(pts_orig, n, progress)
    
    # 闭合多边形
    plot_orig = np.vstack([pts_orig, pts_orig[0]])
    plot_trans = np.vstack([pts_trans, pts_trans[0]])
    
    # 判断相交 (只有在变换基本完成时才判断)
    is_intersect = check_intersection(pts_trans)
    # 如果 progress < 0.9 (还在变换中)，一般不显示红色，除非是演示参数变化的模式(此时progress=1)
    # 简单起见：只要相交就高亮
    highlight = is_intersect and (progress > 0.9)
    de_color = 'red' if highlight else 'green'
    de_width = 5 if highlight else 3
    
    return {
        "n_line_y": [n, n],
        "c_line_x": [c, c],
        "orig_x": plot_orig[:, 0], "orig_y": plot_orig[:, 1],
        "txt_orig_x": [pts_orig[0,0], pts_orig[1,0], pts_orig[2,0]],
        "txt_orig_y": [pts_orig[0,1], pts_orig[1,1], pts_orig[2,1]],
        "trans_x": plot_trans[:, 0], "trans_y": plot_trans[:, 1],
        "txt_trans_x": [pts_trans[0,0], pts_trans[1,0], pts_trans[2,0]],
        "txt_trans_y": [pts_trans[0,1], pts_trans[1,1], pts_trans[2,1]],
        "de_x": [pts_trans[1,0], pts_trans[2,0]], "de_y": [pts_trans[1,1], pts_trans[2,1]],
        "de_color": de_color, "de_width": de_width,
        "c_pos": [c], "c_label_text": [f"c={c:.1f}"]
    }

# ==========================================
# PART C: 侧边栏控制逻辑 (修复变量报错)
# ==========================================
with st.sidebar:
    st.header("🎮 演示控制器")
    
    mode = st.radio(
        "请选择演示模式：",
        ("1️⃣ 演示变换过程 (n型变换)", 
         "2️⃣ 演示点 C 移动 (参数 c)", 
         "3️⃣ 演示参数 n 变化", 
         "4️⃣ 演示旋转角度变化"),
        index=0
    )
    
    st.divider()
    st.markdown("### 🔧 参数设置")

    # 【关键修复1】预先定义所有变量的默认值，防止 NameError
    c_val = 1.0
    n_val = 3.0
    angle_val = 180
    current_progress = 1.0 # 默认变换完成
    
    # 初始化动画参数
    anim_steps = []
    anim_var_name = ""

    # 根据模式覆盖变量值
    if "1️⃣" in mode:
        # 模式1：c, n, angle 固定，progress 动
        c_val = st.slider("点 C 位置 (c)", -5.0, 8.0, 1.0)
        n_val = st.slider("参数 n", 1.0, 5.0, 3.0)
        angle_val = st.slider("旋转角度", 0, 360, 180, 15)
        # 动画变量
        anim_steps = np.linspace(0, 1, 50)
        anim_var_name = "progress"
        
    elif "2️⃣" in mode:
        # 模式2：n, angle 固定，progress=1，c 动
        n_val = st.slider("参数 n", 1.0, 5.0, 3.0)
        angle_val = st.slider("旋转角度", 0, 360, 180, 15)
        # 动画变量
        anim_steps = np.linspace(-4, 8, 60)
        anim_var_name = "c"
        
    elif "3️⃣" in mode:
        # 模式3：c, angle 固定，progress=1，n 动
        c_val = st.slider("点 C 位置 (c)", -5.0, 8.0, 1.0)
        angle_val = st.slider("旋转角度", 0, 360, 180, 15)
        # 动画变量
        anim_steps = np.linspace(1, 6, 50)
        anim_var_name = "n"

    elif "4️⃣" in mode:
        # 模式4：c, n 固定，progress=1，angle 动
        c_val = st.slider("点 C 位置 (c)", -5.0, 8.0, 1.0)
        n_val = st.slider("参数 n", 1.0, 5.0, 3.0)
        # 动画变量
        anim_steps = np.linspace(0, 360, 72)
        anim_var_name = "angle"

# ==========================================
# PART D: 预计算动画帧 (Frames)
# ==========================================
frames = []
for val in anim_steps:
    # 组装参数
    if anim_var_name == "progress":
        params = (c_val, n_val, angle_val, val)
        label = f"{val:.2f}"
    elif anim_var_name == "c":
        params = (val, n_val, angle_val, current_progress)
        label = f"{val:.2f}"
    elif anim_var_name == "n":
        params = (c_val, val, angle_val, current_progress)
        label = f"{val:.2f}"
    elif anim_var_name == "angle":
        params = (c_val, n_val, val, current_progress)
        label = f"{val:.0f}"
        
    d = get_trace_data(*params)
    
    # 【关键修复2】traces=[...]
    # 我们有 9 个图层 (index 0-8)。
    # index 0 是 y=x (静态，不需要在 frame 里更新)。
    # index 1-8 是动态的，需要在 frame 里更新。
    # 必须加上 traces=[1,2,3,4,5,6,7,8] 告诉 Plotly 只更新这些，别动 index 0。
    
    frames.append(go.Frame(
        name=str(val),
        traces=[1, 2, 3, 4, 5, 6, 7, 8], # <--- 核心修复：只更新这些层
        data=[
            go.Scatter(y=d['n_line_y']),                               # [1] 对称轴
            go.Scatter(x=d['c_line_x']),                               # [2] c指示线
            go.Scatter(x=d['orig_x'], y=d['orig_y']),                  # [3] 原三角形
            go.Scatter(x=d['txt_orig_x'], y=d['txt_orig_y']),          # [4] 原顶点字
            go.Scatter(x=d['trans_x'], y=d['trans_y']),                # [5] 变换后三角形
            go.Scatter(x=d['txt_trans_x'], y=d['txt_trans_y']),        # [6] 变换后字
            go.Scatter(x=d['de_x'], y=d['de_y'], line=dict(color=d['de_color'], width=d['de_width'])), # [7] D'E'
            go.Scatter(x=d['c_pos'], text=d['c_label_text'])           # [8] c 标签
        ]
    ))

# 计算初始状态
start_val = anim_steps[0]
if anim_var_name == "progress":
    init_params = (c_val, n_val, angle_val, start_val)
elif anim_var_name == "c":
    init_params = (start_val, n_val, angle_val, current_progress)
elif anim_var_name == "n":
    init_params = (c_val, start_val, angle_val, current_progress)
elif anim_var_name == "angle":
    init_params = (c_val, n_val, start_val, current_progress)

d0 = get_trace_data(*init_params)

# ==========================================
# PART E: 绘制主界面
# ==========================================
st.title("📐 几何变换全能演示系统")

# 理论计算文本
c_min, c_max = calc_c_range(angle_val if anim_var_name!='angle' else start_val, 
                            n_val if anim_var_name!='n' else start_val)
st.markdown(f"**📊 当前状态下 (n={n_val}, $\\theta$={angle_val}°)，使图形相交的 $c$ 的范围是：$[{c_min:.2f}, {c_max:.2f}]$**")

# 构建 Figure
fig = go.Figure(
    data=[
        # --- [0] 永远不动的 y=x (静态层) ---
        go.Scatter(x=[-10, 20], y=[-10, 20], mode='lines', line=dict(color='black', width=1, dash='dash'), name='y=x'),
        
        # --- [1] 对称轴 y=n ---
        go.Scatter(x=[-10, 20], y=d0['n_line_y'], mode='lines', line=dict(color='blue', dash='dashdot'), name='对称轴'),
        
        # --- [2] c 位置指示线 ---
        go.Scatter(x=d0['c_line_x'], y=[-10, 20], mode='lines', line=dict(color='red', width=1, dash='dot'), showlegend=False),
        
        # --- [3] 原三角形 ---
        go.Scatter(x=d0['orig_x'], y=d0['orig_y'], mode='lines+markers', line=dict(color='purple', dash='dot'), name='原像'),
        
        # --- [4] 原顶点字母 ---
        go.Scatter(x=d0['txt_orig_x'], y=d0['txt_orig_y'], mode='text', text=["<b>C</b>","<b>D</b>","<b>E</b>"], 
                   textfont=dict(size=14, color='purple'), textposition="top left", showlegend=False),

        # --- [5] 变换后三角形 ---
        go.Scatter(x=d0['trans_x'], y=d0['trans_y'], mode='lines+markers', fill='toself', fillcolor='rgba(0, 200, 100, 0.3)',
                   line=dict(color='green', width=3), name='变换像'),
        
        # --- [6] 变换后顶点字母 ---
        go.Scatter(x=d0['txt_trans_x'], y=d0['txt_trans_y'], mode='text', text=["<b>C'</b>","<b>D'</b>","<b>E'</b>"], 
                   textfont=dict(size=16, color='black'), textposition="bottom right", showlegend=False),
                   
        # --- [7] D'E' 高亮段 ---
        go.Scatter(x=d0['de_x'], y=d0['de_y'], mode='lines', line=dict(color=d0['de_color'], width=d0['de_width']), name="D'E'"),
        
        # --- [8] c 值标签 ---
        go.Scatter(x=d0['c_pos'], y=[-0.5], mode='text', text=d0['c_label_text'], textfont=dict(color='red', size=12), showlegend=False)
    ],
    frames=frames
)

# 布局设置
fig.update_layout(
    template="simple_white",
    height=700,
    title=dict(text=f"<b>当前演示模式：{mode.split(' ')[1]}</b>", font=dict(size=20, color="black"), x=0.5),
    xaxis=dict(range=[-6, 12], zeroline=True, zerolinecolor='black', gridcolor='#eee', tickfont=dict(color='black')),
    yaxis=dict(range=[-6, 12], scaleanchor="x", scaleratio=1, zeroline=True, zerolinecolor='black', gridcolor='#eee', tickfont=dict(color='black')),
    
    # 动画控件
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        x=0.05, y=0, xanchor="right", yanchor="top",
        bgcolor="white", bordercolor="black", borderwidth=1,
        buttons=[dict(
            label="▶️ 播放动画",
            method="animate",
            args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True)]
        )]
    )],
    
    sliders=[dict(
        steps=[dict(
            method="animate",
            args=[[str(v)], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
            label=f"{v:.1f}"
        ) for v in anim_steps],
        active=0,
        currentvalue=dict(prefix=f"{anim_var_name} : ", font=dict(color="black")),
        pad=dict(t=0),
        font=dict(color="black") # 滑块文字颜色
    )]
)

st.plotly_chart(fig, use_container_width=True)
