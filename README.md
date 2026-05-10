# 🎯 寄宿美高壁球校队 Rating 对比面板

一个基于 Streamlit + Plotly 的交互式数据面板，用于评估申请人在多所美国寄宿高中壁球校队中的相对竞争力。

## ✨ 主要功能

- 🎯 实时调整申请人 Rating，所有图表与排行榜随之刷新
- 👁️ 一键隐藏 G12（即将毕业），评估"明年校队"门槛
- 🏫 学校多选，按需对比目标校
- 📊 各校换血率、剔除 G12 后最高分汇总
- 🏆 壁球特长录取概率排行榜（按概率从高到低，含竞争力档位）
- 📈 自动按 7 校一组拆分分布图，避免单图过宽

## 🚀 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器自动打开 http://localhost:8501 即可。

## 📁 项目结构

```
.
├── app.py                  # 主应用
├── schools_data.csv        # 数据源（直接编辑可增删学校/球员）
├── requirements.txt        # Python 依赖
├── .streamlit/
│   └── config.toml         # 主题配色（绿色 primaryColor）
└── README.md
```

## 📝 数据格式

`schools_data.csv` 的列定义：

| 列名 | 说明 | 示例 |
|---|---|---|
| `School` | 学校名 | `Loomis Chaffee` |
| `Rating` | 球员 Rating（数字）| `4.85` |
| `Grade` | 年级 | `G9` / `G10` / `G11` / `G12` |

新增学校或球员，直接在 CSV 末尾追加行即可，应用会在下次刷新时自动加载。
