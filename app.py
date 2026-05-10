"""
寄宿美高壁球校队 Rating 对比面板
用于评估申请人 Tony 在各目标学校的竞争力
运行方式: streamlit run app.py

数据源：同目录下的 schools_data.csv
    列定义：School, Rating, Grade
    可直接编辑该 CSV 增删学校或球员，应用启动 / 点击「🔄 重新加载数据」即可生效。
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ====================== 1. 页面配置 ======================
st.set_page_config(
    page_title="寄宿美高壁球校队 Rating 对比面板",
    page_icon="🎯",
    layout="wide",
    # 移动端默认收起侧边栏，节省横向空间；桌面端保持展开
    initial_sidebar_state="auto",
    menu_items={
        "About": "寄宿美高壁球校队 Rating 对比面板 · 用于评估申请人 Tony 的相对竞争力",
    },
)

# 自定义 CSS：
# 1) 「全不选」按钮上一抹柔和的琥珀色
# 2) 移动端响应式优化：缩小标题字号、压缩内边距、减少滚动条占用
# 3) 让加粗等元素在窄屏下也清晰可读
st.markdown(
    """
    <style>
    /* ----- 「全不选」按钮：柔和琥珀色 ----- */
    .st-key-btn_clear_all_schools button {
        background-color: #fef3c7 !important;
        color: #92400e !important;
        border: 1px solid #fcd34d !important;
    }
    .st-key-btn_clear_all_schools button:hover {
        background-color: #fde68a !important;
        color: #78350f !important;
        border-color: #f59e0b !important;
    }

    /* ----- 桌面端：让主区域两侧留点呼吸空间但不浪费 ----- */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* ----- 移动端响应式（屏宽 < 768px 时生效）----- */
    @media (max-width: 768px) {
        /* 主区域内边距压缩，给图表更多空间 */
        .block-container {
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            padding-top: 0.8rem !important;
        }
        /* 主标题缩小，避免占满整屏 */
        h1 {
            font-size: 1.4rem !important;
            line-height: 1.3 !important;
        }
        h2 {
            font-size: 1.15rem !important;
        }
        h3, h4 {
            font-size: 1rem !important;
        }
        /* 表格在移动端允许横向滚动而不是溢出 */
        [data-testid="stDataFrame"] {
            overflow-x: auto !important;
        }
        /* 缩小数据表的行高，让"完整展开"在小屏上仍然紧凑 */
        [data-testid="stDataFrame"] [role="row"] {
            min-height: 30px !important;
        }
        /* 关键指标的文本不要换行截断 */
        .stMarkdown p {
            word-break: break-word !important;
        }
    }

    /* ----- 超窄屏（< 480px，小手机）：进一步压缩 ----- */
    @media (max-width: 480px) {
        h1 {
            font-size: 1.2rem !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] {
            font-size: 0.75rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ====================== 2. 常量与路径 ======================
DATA_PATH = Path(__file__).parent / "schools_data.csv"

GRADE_ORDER = ["G9", "G10", "G11", "G12"]
COLOR_MAP = {
    "G9": "#1f77b4",   # 蓝
    "G10": "#2ca02c",  # 绿
    "G11": "#ff7f0e",  # 橙
    "G12": "#d62728",  # 红
}
DEFAULT_TONY_RATING = 4.48


# ====================== 3. 数据加载 ======================
# 注意：这里故意不使用 @st.cache_data。原因是 CSV 体积极小（几十~几百行），
# 每次脚本 rerun 直接读取即可，避免任何缓存导致"修改 CSV 后页面不刷新"的问题。
def get_data() -> pd.DataFrame:
    """读取 CSV 数据并做基础清洗；文件不存在时给出明确报错。"""
    if not DATA_PATH.exists():
        st.error(
            f"未找到数据文件：`{DATA_PATH.name}`。请在与 app.py 同目录下创建该 CSV，"
            "并包含表头 `School, Rating, Grade`。"
        )
        st.stop()
    df = pd.read_csv(DATA_PATH)
    # 容错：去除空行 / 字符串两端空白；保证类型正确
    df = df.dropna(subset=["School", "Rating", "Grade"]).copy()
    df["School"] = df["School"].astype(str).str.strip()
    df["Grade"] = df["Grade"].astype(str).str.strip().str.upper()
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df = df.dropna(subset=["Rating"]).reset_index(drop=True)
    return df


def build_summary(df: pd.DataFrame, school_order: list) -> pd.DataFrame:
    """计算每所学校的汇总指标：总人数、G12 人数、换血率、剔除 G12 后的最高分。"""
    if df.empty:
        return pd.DataFrame(columns=["学校", "校队总人数", "即将毕业 (G12) 人数", "换血率 (%)", "剔除 G12 后最高分"])

    summary_rows = []
    for school in school_order:
        group = df[df["School"] == school]
        if group.empty:
            continue
        total = len(group)
        g12_count = int((group["Grade"] == "G12").sum())
        turnover = (g12_count / total * 100) if total > 0 else 0.0
        non_g12 = group[group["Grade"] != "G12"]["Rating"]
        top_non_g12 = float(non_g12.max()) if not non_g12.empty else None

        summary_rows.append({
            "学校": school,
            "校队总人数": total,
            "即将毕业 (G12) 人数": g12_count,
            "换血率 (%)": round(turnover, 1),
            "剔除 G12 后最高分": round(top_non_g12, 2) if top_non_g12 is not None else None,
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_df = summary_df.sort_values(by="换血率 (%)", ascending=False).reset_index(drop=True)
    return summary_df


# ====================== 4. 会话状态初始化 ======================
if "tony_rating" not in st.session_state:
    st.session_state.tony_rating = DEFAULT_TONY_RATING


# ====================== 5. 加载完整数据 ======================
full_df = get_data()
ALL_SCHOOLS = list(dict.fromkeys(full_df["School"].tolist()))  # 去重并保留 CSV 中的原始顺序

# 为每所学校初始化对应的复选框 session_state（默认全部勾选）
# 使用 f"school_check_{name}" 作为 key，使每个复选框有独立的、稳定的状态
def _school_key(name: str) -> str:
    return f"school_check_{name}"

for _s in ALL_SCHOOLS:
    if _school_key(_s) not in st.session_state:
        st.session_state[_school_key(_s)] = True


# ====================== 6. 侧边栏：参数 & 学校选取 ======================
with st.sidebar:
    st.header("⚙️ 控制面板")

    # ---------- 6.1 Tony 分数调整 ----------
    st.subheader("🎯 申请人 Tony 的 Rating")
    st.number_input(
        label="实时调整 Tony 的 Rating（基准红线会随之移动）",
        min_value=0.0,
        max_value=10.0,
        step=0.01,
        format="%.2f",
        key="tony_rating",
        help="可输入任意分数，例如 4.48、4.5、5.0 等，图表与统计会即时更新。",
    )

    # ---------- 6.2 视图过滤 ----------
    st.subheader("👁️ 视图过滤")
    hide_g12 = st.checkbox(
        "🎓 隐藏即将毕业的 12 年级学生 (G12)",
        value=False,
        help="勾选后将从图表中过滤掉 G12 学生，便于预估明年校队的真实门槛。",
    )

    # ---------- 6.3 学校选取 ----------
    st.subheader("🏫 学校选取")

    # 使用 on_click 回调模式批量修改各复选框的 session_state；
    # 回调在下一次脚本运行的"widget 渲染之前"执行，因此可以安全修改与 widget 绑定的 key。
    def _select_all_schools() -> None:
        for s in ALL_SCHOOLS:
            st.session_state[_school_key(s)] = True

    def _clear_all_schools() -> None:
        for s in ALL_SCHOOLS:
            st.session_state[_school_key(s)] = False

    col_a, col_b = st.columns(2)
    with col_a:
        # 「全选」使用 primary 类型 → 套用主题主色（绿色），与勾选态颜色一致
        st.button(
            "✅ 全选",
            use_container_width=True,
            on_click=_select_all_schools,
            type="primary",
            key="btn_select_all_schools",
        )
    with col_b:
        # 「全不选」使用 secondary 类型 → 默认浅灰，明显区别于「全选」
        st.button(
            "❎ 全不选",
            use_container_width=True,
            on_click=_clear_all_schools,
            type="secondary",
            key="btn_clear_all_schools",
        )

    # 当前已选数量（用于展开器标题，便于在折叠状态也能看到选了几所）
    _checked_count = sum(1 for s in ALL_SCHOOLS if st.session_state.get(_school_key(s), True))

    # 下拉式展开器：每所学校单独一行，后跟一个复选框
    with st.expander(f"📋 选择学校（已选 {_checked_count} / {len(ALL_SCHOOLS)} 所）", expanded=True):
        for s in ALL_SCHOOLS:
            st.checkbox(s, key=_school_key(s))

    st.markdown("---")

    # ---------- 6.4 数据管理 ----------
    st.subheader("📁 数据源")
    # 展示文件修改时间，方便用户验证当前页面用的是不是最新版 CSV
    _mtime = datetime.fromtimestamp(DATA_PATH.stat().st_mtime)
    st.markdown(
        f"📄 数据文件：`{DATA_PATH.name}`  \n"
        f"🏫 共 **{len(ALL_SCHOOLS)}** 所学校  \n"
        f"👥 共 **{len(full_df)}** 条球员记录  \n"
        f"🕒 文件更新于：`{_mtime.strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    st.caption(
        "👉 直接编辑同目录下的 `schools_data.csv`（增删学校或球员），保存后点击下方按钮即可刷新。"
    )
    if st.button("🔄 重新加载数据", use_container_width=True):
        # 数据已经无缓存、每次 rerun 实时读取，这里只需触发一次 rerun 即可
        st.toast("✅ 已重新加载最新数据", icon="🔄")
        st.rerun()


# ====================== 7. 主体界面 ======================
TONY_RATING = float(st.session_state.tony_rating)
# 从各复选框的 session_state 中聚合出"当前已选学校"，并保留 CSV 中的原始顺序
SCHOOL_ORDER = [s for s in ALL_SCHOOLS if st.session_state.get(_school_key(s), True)]

st.title("🎯 寄宿美高壁球校队 Rating 对比面板")
st.caption(
    f"对比申请人 **Tony (Rating: {TONY_RATING:.2f})** 在 "
    f"**{len(SCHOOL_ORDER)} / {len(ALL_SCHOOLS)}** 所目标寄宿高中壁球校队中的相对竞争力。"
)

# 根据"学校多选"过滤完整数据
df = full_df[full_df["School"].isin(SCHOOL_ORDER)].copy()
plot_df = df[df["Grade"] != "G12"].copy() if hide_g12 else df.copy()


# ====================== 8. 分布图 (Plotly) ======================
if df.empty:
    st.warning("当前未选中任何学校，请在左侧侧边栏「🏫 学校选取」展开菜单中至少勾选 1 所学校。")
else:
    # ----- 计算所有子图共享的 Y 轴范围（保证视觉一致，便于横向对比）-----
    # 默认 [3.0, 7.0]（满足"防止 Checkbox 切换跳动"的稳定性需求）；
    # 若 CSV 中新加入的学校有球员 Rating 超出该区间，则自动扩展。
    if not df.empty:
        data_min = float(df["Rating"].min())
        data_max = float(df["Rating"].max())
        y_min = min(3.0, data_min - 0.2)
        y_max = max(7.0, data_max + 0.2)
    else:
        y_min, y_max = 3.0, 7.0

    # ----- 把 SCHOOL_ORDER 切成多组，每组最多 SCHOOLS_PER_CHART 所学校 -----
    SCHOOLS_PER_CHART = 7
    school_chunks = [
        SCHOOL_ORDER[i : i + SCHOOLS_PER_CHART]
        for i in range(0, len(SCHOOL_ORDER), SCHOOLS_PER_CHART)
    ]

    for chunk_idx, chunk in enumerate(school_chunks, start=1):
        chunk_plot_df = plot_df[plot_df["School"].isin(chunk)]

        # 多组时在标题里标注分组信息，单组时不显示赘述
        if len(school_chunks) > 1:
            chart_title = (
                f"各校壁球校队 Rating 分布（按年级着色）"
                f" — 第 {chunk_idx} / {len(school_chunks)} 组"
            )
        else:
            chart_title = "各校壁球校队 Rating 分布（按年级着色）"

        fig = px.strip(
            chunk_plot_df,
            x="School",
            y="Rating",
            color="Grade",
            category_orders={"School": chunk, "Grade": GRADE_ORDER},
            color_discrete_map=COLOR_MAP,
            stripmode="overlay",
            # 精简 hover 字段，减少传输到前端的数据量
            hover_data={"Rating": ":.2f", "Grade": True, "School": False},
            title=chart_title,
        )

        # 散点样式：移动端会通过 layout autosize 自动适配宽度
        fig.update_traces(
            marker=dict(size=11, opacity=0.85, line=dict(width=1, color="white")),
            jitter=0.4,
        )

        # Y 轴：标题「Rating」加粗
        fig.update_yaxes(
            range=[y_min, y_max],
            title=dict(text="<b>Rating</b>", font=dict(size=16)),
            tickfont=dict(size=13),
            gridcolor="#e5e5e5",
            automargin=True,
        )
        # X 轴：去掉「学校」标题；学校名加粗 + 自动旋转避免重叠
        fig.update_xaxes(
            title=None,
            tickfont=dict(size=14, color="#1f2937", family="Arial Black, sans-serif"),
            tickangle=0,
            automargin=True,
        )

        # Tony 的水平基准线 + 右侧注释（位置随 Tony 分数实时移动）
        fig.add_hline(
            y=TONY_RATING,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text=f"Tony ({TONY_RATING:.2f})",
            annotation_position="right",
            annotation_font_color="red",
            annotation_font_size=13,
        )

        fig.update_layout(
            # 高度按学校数量微调，单图永远适应屏幕
            height=520,
            autosize=True,
            legend=dict(
                title_text="年级",
                orientation="h",        # 横向图例（移动端节省纵向空间）
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            plot_bgcolor="white",
            title_font_size=16,
            margin=dict(l=50, r=30, t=70, b=50),  # 右边距收紧
            hovermode="closest",
        )

        # 关键性能优化：
        # 1) displayModeBar=False     → 隐藏 Plotly 顶部工具栏（少加载~100KB JS + 减少渲染）
        # 2) staticPlot=False         → 保留 hover 交互，但禁用复杂动效
        # 3) responsive=True          → 跟随容器宽度变化自适应（移动端关键）
        # 4) scrollZoom=False         → 禁用滚轮缩放，避免移动端误触
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
                "scrollZoom": False,
                "staticPlot": False,
            },
        )

    # ====================== 9. 数据汇总表 ======================
    st.subheader("📊 各校换血率与竞争门槛分析")
    st.caption(
        "换血率越高，说明明年校队空缺越大，对 Tony 越有利；"
        "「剔除 G12 后最高分」可视为明年校队的真实顶端水平。"
    )

    summary_df = build_summary(df, SCHOOL_ORDER)

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "校队总人数": st.column_config.NumberColumn(format="%d 人"),
            "即将毕业 (G12) 人数": st.column_config.NumberColumn(format="%d 人"),
            "换血率 (%)": st.column_config.ProgressColumn(
                "换血率 (%)",
                help="G12 人数 / 校队总人数",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
            "剔除 G12 后最高分": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    # ====================== 10. 关键洞察 ======================
    st.markdown("---")
    st.subheader(f"💡 关键洞察（基于 Tony Rating = {TONY_RATING:.2f}）")
    st.caption(
        "下方两栏的排名会随侧边栏 Tony Rating 实时刷新；"
        "若调整后排名未变，说明在新分数下学校之间的相对位置确实没有改变。"
    )

    col_best, col_hardest = st.columns(2)

    # 各校剔除 G12 后的人数 & Tony 能击败的人数 → 用于评估录取机会
    non_g12_df = df[df["Grade"] != "G12"]
    if not non_g12_df.empty:
        per_school = (
            non_g12_df.groupby("School")
            .apply(lambda g: pd.Series({
                "beatable": int((g["Rating"] < TONY_RATING).sum()),
                "total_non_g12": len(g),
            }))
            .reindex(SCHOOL_ORDER)
            .dropna()
        )
        per_school["beat_ratio"] = per_school["beatable"] / per_school["total_non_g12"]

        best_sorted = per_school.sort_values(
            by=["beat_ratio", "beatable"], ascending=[False, False]
        )
        top2_best = best_sorted.head(2)

        hardest_sorted = per_school.sort_values(
            by=["beat_ratio", "beatable"], ascending=[True, True]
        )
        top2_hardest = hardest_sorted.head(2)
    else:
        per_school = pd.DataFrame(columns=["beatable", "total_non_g12", "beat_ratio"])
        top2_best = pd.DataFrame()
        top2_hardest = pd.DataFrame()

    with col_best:
        st.markdown("#### 🌟 最具机会的学校（剔除 G12，前 2 所）")
        st.caption(
            f"按「Rating < {TONY_RATING:.2f} 的非毕业球员占比」从高到低排序；"
            "并列时优先可击败人数更多的学校。"
        )
        if top2_best.empty:
            st.info("暂无数据（无非 G12 球员）。")
        else:
            for rank, (school, row) in enumerate(top2_best.iterrows(), start=1):
                ratio_pct = row["beat_ratio"] * 100
                st.markdown(
                    f"**{rank}. {school}** — 可压制 **{int(row['beatable'])}** / "
                    f"**{int(row['total_non_g12'])}** 人（**{ratio_pct:.1f}%**）"
                )

    with col_hardest:
        st.markdown("#### 🧱 壁球录取几率最低的学校（前 2 所）")
        st.caption(
            f"按「Rating < {TONY_RATING:.2f} 的非毕业球员占比」从低到高排序；"
            "占比越低进入校队越难，并列时优先可击败人数更少的学校。"
        )
        if top2_hardest.empty:
            st.info("暂无数据（无非 G12 球员）。")
        else:
            for rank, (school, row) in enumerate(top2_hardest.iterrows(), start=1):
                ratio_pct = row["beat_ratio"] * 100
                st.markdown(
                    f"**{rank}. {school}** — 仅可压制 **{int(row['beatable'])}** / "
                    f"**{int(row['total_non_g12'])}** 人（**{ratio_pct:.1f}%**）"
                )

    # ---------- 10.1 全量录取概率排行榜 ----------
    st.markdown("---")
    st.markdown("#### 🏆 壁球特长录取概率排行榜（按概率从高到低）")
    st.caption(
        f"录取概率 = Tony 能击败的非毕业球员 / 该校非毕业球员总数（基于 Rating < {TONY_RATING:.2f}）。"
        "排名越靠前，Tony 凭借壁球特长进入该校的可能性越大。"
    )

    if per_school.empty:
        st.info("暂无可排名的数据（无非 G12 球员）。")
    else:
        rank_df = (
            per_school
            .sort_values(by=["beat_ratio", "beatable"], ascending=[False, False])
            .reset_index()
            .rename(columns={"School": "学校"})
        )
        rank_df.insert(0, "排名", range(1, len(rank_df) + 1))
        rank_df["可击败人数"] = rank_df["beatable"].astype(int)
        rank_df["非G12总人数"] = rank_df["total_non_g12"].astype(int)
        rank_df["录取概率 (%)"] = (rank_df["beat_ratio"] * 100).round(1)

        # 直观的星级评估：>=70% 优势 / 40-70% 中等 / <40% 困难
        def _stars(ratio: float) -> str:
            if ratio >= 0.7:
                return "🟢 优势"
            elif ratio >= 0.4:
                return "🟡 中等"
            else:
                return "🔴 困难"
        rank_df["竞争力评估"] = rank_df["beat_ratio"].apply(_stars)

        rank_display = rank_df[["排名", "学校", "可击败人数", "非G12总人数", "录取概率 (%)", "竞争力评估"]]

        # 计算精确高度：表头约 38px + 每行 35px + 底部余量 3px，
        # 这样无论学校数量多少都能完整展开，去掉右侧的纵向滚动条。
        ROW_H = 35
        HEADER_H = 38
        table_height = HEADER_H + ROW_H * len(rank_display) + 3

        st.dataframe(
            rank_display,
            use_container_width=True,
            hide_index=True,
            height=table_height,
            column_config={
                "排名": st.column_config.NumberColumn(width="small"),
                "可击败人数": st.column_config.NumberColumn(format="%d 人"),
                "非G12总人数": st.column_config.NumberColumn(format="%d 人"),
                "录取概率 (%)": st.column_config.ProgressColumn(
                    "录取概率 (%)",
                    help=f"Rating < {TONY_RATING:.2f} 的非毕业球员占该校非毕业球员的比例",
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                ),
                "竞争力评估": st.column_config.TextColumn(width="small"),
            },
        )

    with st.expander("📋 查看明细数据（当前视图）"):
        st.dataframe(plot_df.reset_index(drop=True), use_container_width=True, hide_index=True)
