import streamlit as st
import numpy as np
import plotly.graph_objects as go # 引入 Plotly 的图表对象

# --- 1. 页面配置 ---
st.set_page_config(page_title="几何变换演示课堂", layout="wide")

# ==============================================
# 【区域 A】: 请把你的几何计算函数粘贴到这里
# ==============================================
# 这里的代码是我为了演示写的假数据。
# 你需要用你原来的 get_triangle_CDE 等函数替换掉下面这个函数。

def 你的几何计算函数(progress, c_val, n_val, angle_val):
    """
    这是一个占位函数，请用你自己的真实计算逻辑替换它。
    目标是返回三角形三个顶点的坐标。
    """
    # --- 这是一个模拟的运动轨迹，仅供演示 ---
    # 模拟点 C 在 y=x 上移动
    xc = c_val + progress * 2
    yc = c_val + progress * 2
    
    # 模拟一个简单的三角形绕点 C 旋转
    theta = np.radians(angle_val)
    # 定义一个初始小三角形（相对于 C 点）
    base_triangle = np.array([[0, 0], [2, 0], [1, 1.732]]) * n_val/3 # 根据 n 缩放
    
    # 旋转矩阵
    rot_matrix = np.array([[np.cos(theta), -np.sin(theta)],
                           [np.sin(theta),  np.cos(theta)]])
    
    # 旋转并平移到 C 点
    rotated_triangle = base_triangle.dot(rot_matrix.T)
    final_triangle = rotated_triangle + np.array([xc, yc])
    
    # 为了画闭合多边形，把第一个点再加到最后
    final_triangle_closed = np.vstack([final_triangle, final_triangle[0]])
    
    return final_triangle_closed, xc, yc
# ==============================================
# 【区域 A 结束】
# ==============================================


# --- 2. 侧边栏：控制面板 (中文) ---
with st.sidebar:
    st.header("🎮 控制面板")
    st.write("调整参数观察几何变换")
    
    # 进度滑块
    progress = st.slider("▶️ 变换进度 (n型变换)", 0.0, 1.0, 0.5, 0.01)
    st.divider() # 分割线

    # 参数滑块
    c_val = st.slider("🅰️ 点 C 位置 (参数 c)", -5.0, 8.0, 4.0, 0.1)
    n_val = st.slider("🅱️ 参数 n (缩放大小)", 1.0, 5.0, 3.0, 0.1)
    angle_val = st.slider("🔄 旋转角度", 0, 360, 45, 1)


# --- 3. 主体界面 ---
st.title("📐 初中数学：n型对照变换动态演示")
st.markdown("### 观察思考：随着参数变化，三角形的顶点轨迹有何规律？")

# 调用计算函数，获取数据
# 【重要】：如果你替换了上面的函数，记得这里调用的名字也要改
triangle_coords, xc_now, yc_now = 你的几何计算函数(progress, c_val, n_val, angle_val)


# --- 4. Plotly 画图核心逻辑 (全新的部分) ---

# 创建一个空白画布
fig = go.Figure()

# [图层1]: 画辅助线 y=x
fig.add_trace(go.Scatter(
    x=[-10, 20], y=[-10, 20],
    mode='lines',
    name='辅助线 y=x',
    line=dict(color='gray', width=2, dash='dash') # 灰色虚线
))

# [图层2]: 画当前的 C 点位置提示线
fig.add_trace(go.Scatter(
    x=[xc_now, xc_now], y=[-10, 20],
    mode='lines',
    name=f'当前C点横坐标={xc_now:.1f}',
    line=dict(color='red', width=1, dash='dot'), # 红色细点划线
    hoverinfo='skip' # 鼠标放上去不显示信息，避免干扰
))

# [图层3]: 画三角形 (核心)
fig.add_trace(go.Scatter(
    x=triangle_coords[:, 0], # 所有顶点的 X 坐标
    y=triangle_coords[:, 1], # 所有顶点的 Y 坐标
    fill='toself', # 填充闭合区域
    fillcolor='rgba(0, 200, 100, 0.5)', # 半透明绿色填充
    line=dict(color='green', width=3), # 绿色边框线条
    name='变换三角形 (目标)',
    mode='lines+markers', # 显示线和顶点
    marker=dict(size=8) # 顶点大小
))


# --- 5. 设置画布布局 (关键步骤) ---
# 这一步是为了让几何图形不变形，正方形看起来就是正方形
fig.update_layout(
    # 设置标题和字体大小
    title=dict(text="几何变换平面直角坐标系", font=dict(size=20)),
    # 设置 X 轴和 Y 轴的范围 (固定范围，防止画面跳动)
    xaxis=dict(range=[-8, 18], title="X 轴", zeroline=True, gridcolor='lightgray'),
    yaxis=dict(range=[-5, 15], title="Y 轴", zeroline=True, gridcolor='lightgray',
               scaleanchor="x", scaleratio=1), # 【重要】强制 XY 轴比例 1:1
    # 设置画布大小和背景色
    width=800, height=800,
    plot_bgcolor='white',
    hovermode='closest', # 鼠标悬停模式
    # 图例位置
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor='rgba(255,255,255,0.8)')
)

# --- 6. 在 Streamlit 中显示 Plotly 图表 ---
# use_container_width=True 让图表自适应网页宽度
st.plotly_chart(fig, use_container_width=True)
