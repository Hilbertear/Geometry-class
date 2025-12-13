import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 页面配置 (宽屏 + 默认侧边栏展开) ---
st.set_page_config(
    page_title="几何变换全能演示",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# PART A: 数学核心逻辑 (保持不变)
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
# PART B: 通用绘图数据生成器 (核心黑科技)
# ==========================================
# 这个函数负责生成某一瞬间所有的线条、点、文字
# 无论哪个参数在变，最后都调用这个函数来画图
def get_trace_data(c, n, angle, progress):
    # 1. 计算
    pts_orig = get_triangle_CDE(c, angle)
    pts_trans = apply_n_transform(pts_orig, n, progress)
    
    # 闭合多边形
    plot_orig = np.vstack([pts_orig, pts_orig[0]])
    plot_trans = np.vstack([pts_trans, pts_trans[0]])
    
    # 判断相交
    is_intersect = check_intersection(pts_trans)
    # 只有在变换基本完成且相交时才变红
    highlight = is_intersect and (progress > 0.9)
    de_color = 'red' if highlight else 'green'
    de_width = 5 if highlight else 3
    
    # 返回一个字典，包含所有图层的数据
    return {
        "orig_x": plot_orig[:, 0], "orig_y": plot_orig[:, 1],
        "trans_x": plot_trans[:, 0], "trans_y": plot_trans[:, 1],
        "de_x": [pts_trans[1,0], pts_trans[2,0]], "de_y": [pts_trans[1,1], pts_trans[2,1]],
        "de_color": de_color, "de_width": de_width,
        "n_line_y": [n, n],
        "c_line_x": [c, c],
        "c_label_text": [f"c={c:.1f}"],
        "c_pos": [c],
        # 顶点字母位置 (动态更新)
        "txt_orig_x": [pts_orig[0,0], pts_orig[1,0], pts_orig[2,0]],
        "txt_orig_y": [pts_orig[0,1], pts_orig[1,1], pts_orig[2,1]],
        "txt_trans_x": [pts_trans[0,0], pts_trans[1,0], pts_trans[2,0]],
        "txt_trans_y": [pts_trans[0,1], pts_trans[1,1], pts_trans[2,1]],
    }

# ==========================================
# PART C: 侧边栏控制逻辑
# ==========================================
with st.sidebar:
    st.header("🎮 演示控制器")
    
    # 1. 模式选择
    mode = st.radio(
        "请选择演示模式：",
        ("1️⃣ 演示变换过程 (n型变换)", 
         "2️⃣ 演示点 C 移动 (参数 c)", 
         "3️⃣ 演示参数 n 变化", 
         "4️⃣ 演示旋转角度变化"),
        index=0
    )
    
    st.divider()
    st.markdown("### 🔧 静态参数设置")
    st.info("下方滑块用于设置**不参与动画**的参数")

    # 根据模式显示不同的滑块 (被选中的参数会自动隐藏，避免冲突)
    if "1️⃣" in mode:
        # 演示变换：c, n, angle 固定，progress 动
        c_val = st.slider("点 C 位置 (c)", -5.0, 8.0, 1.0)
        n_val = st.slider("参数 n", 1.0, 5.0, 3.0)
        angle_val = st.slider("旋转角度", 0, 360, 180, 15)
        # 动画变量范围
        anim_steps = np.linspace(0, 1, 50)
        anim_var_name = "progress"
        
    elif "2️⃣" in mode:
        # 演示 C 移动：n, angle 固定，progress 锁定为 1 (看结果)，c 动
        n_val = st.slider("参数 n", 1.0, 5.0, 3.0)
        angle_val = st.slider("旋转角度", 0, 360, 180, 15)
        # 默认变换完成，否则看不出相交
        current_progress = 1.0 
        # 动画变量范围
        anim_steps = np.linspace(-4, 8, 60) # c 从 -4 走到 8
        anim_var_name = "c"
        
    elif "3️⃣" in mode:
        # 演示 n 变化：c, angle 固定，progress=1，n 动
        c_val = st.slider("点 C 位置 (c)", -5.0, 8.0, 1.0)
        angle_val = st.slider("旋转角度", 0, 360, 180, 15)
        current_progress = 1.0
        # 动画变量范围
        anim_steps = np.linspace(1, 6, 50) # n 从 1 走到 6
        anim_var_name = "n"

    elif "4️⃣" in mode:
        # 演示旋转：c, n 固定，progress=1，angle 动
        c_val = st.slider("点 C 位置 (c)", -5.0, 8.0, 1.0)
        n_val = st.slider("参数 n", 1.0, 5.0, 3.0)
        current_progress = 1.0
        # 动画变量范围
        anim_steps = np.linspace(0, 360, 72) # 0 到 360度
        anim_var_name = "angle"

# ==========================================
# PART D: 预计算动画帧 (Frames)
# ==========================================
frames = []
for val in anim_steps:
    # 根据当前模式，组装参数
    if anim_var_name == "progress":
        params = (c_val, n_val, angle_val, val)
        frame_label = f"进度 {val:.2f}"
    elif anim_var_name == "c":
        params = (val, n_val, angle_val, current_progress)
        frame_label = f"c={val:.2f}"
    elif anim_var_name == "n":
        params = (c_val, val, angle_val, current_progress)
        frame_label = f"n={val:.2f}"
    elif anim_var_name == "angle":
        params = (c_val, n_val, val, current_progress)
        frame_label = f"ang={val:.0f}"
        
    # 获取绘图数据
    d = get_trace_data(*params)
    
    # 创建 Frame
    frames.append(go.Frame(
        name=str(val), # 关键：用于 slider 绑定
        data=[
            go.Scatter(y=d['n_line_y']),      # [1] 对称轴
            go.Scatter(x=d['c_line_x']),      # [2] c指示线
            go.Scatter(x=d['orig_x'], y=d['orig_y']), # [3] 原三角形
            go.Scatter(x=d['txt_orig_x'], y=d['txt_orig_y']), # [4] 原顶点字
            go.Scatter(x=d['trans_x'], y=d['trans_y']), # [5] 变换后三角形
            go.Scatter(x=d['txt_trans_x'], y=d['txt_trans_y']), # [6] 变换后字
            go.Scatter(x=d['de_x'], y=d['de_y'], line=dict(color=d['de_color'], width=d['de_width'])), # [7] D'E'
            go.Scatter(x=d['c_pos'], text=d['c_label_text']) # [8] c 标签
        ]
    ))

# 计算初始状态 (取动画第一帧的值)
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

# 显示当前理论计算范围 (仅在 c 模式下显示，或者一直显示)
c_min, c_max = calc_c_range(angle_val if anim_var_name!='angle' else start_val, 
                            n_val if anim_var_name!='n' else start_val)
st.markdown(f"**📊 当前状态下 (n={n_val}, $\\theta$={angle_val}°)，使图形相交的 $c$ 的范围是：$[{c_min:.2f}, {c_max:.2f}]$**")

# 构建 Figure
fig = go.Figure(
    data=[
        # [0] 永远不动的 y=x (不需要在 frame 里更新)
        go.Scatter(x=[-10, 20], y=[-10, 20], mode='lines', line=dict(color='black', width=1, dash='dash'), name='y=x'),
        
        # [1] 对称轴 y=n
        go.Scatter(x=[-10, 20], y=d0['n_line_y'], mode='lines', line=dict(color='blue', dash='dashdot'), name='对称轴'),
        
        # [2] c 位置指示线
        go.Scatter(x=d0['c_line_x'], y=[-10, 20], mode='lines', line=dict(color='red', width=1, dash='dot'), showlegend=False),
        
        # [3] 原三角形
        go.Scatter(x=d0['orig_x'], y=d0['orig_y'], mode='lines+markers', line=dict(color='purple', dash='dot'), name='原像'),
        
        # [4] 原三角形顶点字母 (单独图层为了位置准确)
        go.Scatter(x=d0['txt_orig_x'], y=d0['txt_orig_y'], mode='text', text=["<b>C</b>","<b>D</b>","<b>E</b>"], 
                   textfont=dict(size=14, color='purple'), textposition="top left", showlegend=False),

        # [5] 变换后三角形
        go.Scatter(x=d0['trans_x'], y=d0['trans_y'], mode='lines+markers', fill='toself', fillcolor='rgba(0, 200, 100, 0.3)',
                   line=dict(color='green', width=3), name='变换像'),
        
        # [6] 变换后顶点字母
        go.Scatter(x=d0['txt_trans_x'], y=d0['txt_trans_y'], mode='text', text=["<b>C'</b>","<b>D'</b>","<b>E'</b>"], 
                   textfont=dict(size=16, color='black'), textposition="bottom right", showlegend=False),
                   
        # [7] D'E' 高亮段
        go.Scatter(x=d0['de_x'], y=d0['de_y'], mode='lines', line=dict(color=d0['de_color'], width=d0['de_width']), name="D'E'"),
        
        # [8] c 值标签 (放在x轴附近)
        go.Scatter(x=d0['c_pos'], y=[-0.5], mode='text', text=d0['c_label_text'], textfont=dict(color='red', size=12), showlegend=False)
    ],
    frames=frames
)

# 布局设置 (强制白底黑字)
fig.update_layout(
    template="simple_white", # 核心：白底模板
    height=700,
    title=dict(text=f"<b>当前演示模式：{mode.split(' ')[1]}</b>", font=dict(size=20), x=0.5),
    xaxis=dict(range=[-6, 12], zeroline=True, zerolinecolor='black', gridcolor='#eee'),
    yaxis=dict(range=[-6, 12], scaleanchor="x", scaleratio=1, zeroline=True, zerolinecolor='black', gridcolor='#eee'),
    
    # 动画控件
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        x=0.05, y=0, xanchor="right", yanchor="top",
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
        currentvalue=dict(prefix=f"{anim_var_name} : "),
        pad=dict(t=0),
    )]
)

st.plotly_chart(fig, use_container_width=True)
