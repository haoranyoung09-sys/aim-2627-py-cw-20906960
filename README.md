# AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块

> **全部题目、规范、评分、提交见 [题面.pdf](题面.pdf)。** 本 README 只讲怎么把环境跑起来；没在这里出现的规格细节，一律以题面为准。

## 1. 环境要求

- Python 3.8+，仅标准库（不允许第三方运行时依赖）；
- 开发工具只需 `pytest`（测试）与 `autopep8`（风格，CI 会检查）；
- VS Code 打开仓库会推荐安装 `ms-python.autopep8` 插件（`.vscode/extensions.json`），保存即格式化即可过风格检查。

## 2. 快速开始

```bash
# 1. 用 GitHub 的 Use this template 创建你自己的仓库，然后 clone
git clone https://github.com/<你的用户名>/<你的仓库>.git
cd <你的仓库>   # 直接在 main 分支上开发

# 创建虚拟环境

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. 装依赖
python -m pip install pytest autopep8

# 3. 启用 AI 会话归档钩子（课程要求，见下方第 3 节）
python -m pip install 'agent-session-commit[pre-commit]==0.1.3' -i https://pypi.org/simple
agent-session-commit install --pre-commit   # 交互选择你的 AI 助手与会话目录

# 4. 跑测试（刚到手：全部 skip，CI 是绿的）
python -m pytest

# 5. 看演示
python main.py

# 6. 打开 题面.pdf 读题，开始实现 src/main/__init__.py 里的 TODO
```

## 3. AI 会话归档（pre-commit）

本课程允许使用 AI，提交的 commit 需要携带 AI 会话归档作为透明化记录：每次 `git commit` 后，钩子会把新增会话自动 amend 进同一个提交（`.agent-sessions/bundles/`），不产生额外的归档提交。支持 Claude Code、OpenAI Codex CLI、GitHub Copilot CLI、Qoder、ZCode、Trae、Tencent CodeBuddy 等（完整名单见 [AgentLedger](https://github.com/Gentle-Lijie/AgentLedger)）。

- 配置是仓库本地的：每个 clone 运行一次 `agent-session-commit install --pre-commit`，方向键选择 agent、确认其会话目录即可；
- 不想用 TUI 可手动配置：`git config --local agent-session.agent claude`、`git config --local agent-session.source "<会话目录>"`，然后 `python -m pip install 'pre-commit>=3.2.0' && pre-commit install`；
- 归档是普通 Git 内容且会推送到公开仓库——不要在 AI 会话里粘贴令牌等敏感信息；
- 换了 agent 或目录就重跑一次安装命令；卸载：从 `.pre-commit-config.yaml` 移除该条目后重跑 `pre-commit install`。

## 4. 本地开发循环

- **写代码**：全部作业在 `src/main/__init__.py`，按题面各题规范补全每个标有 TODO 的函数；注释里标注了对应的题面主题，推荐顺序 Q1 → Q6。
- **跑测试**：`python -m pytest` —— 可见测试是规格书的一部分，未实现的函数自动 skip，实现一个、对应测试亮一个。本地全绿 ≠ 满分（见题面）。
- **看演示**：`python main.py`（等价于 `PYTHONPATH=src python -m main`），随实现进度逐段点亮，不进测试。
- **Q6 自测**：`python tools/run_seeds.py --q6`（200 张固定地图统计），单 seed 渲染 `python tools/run_seeds.py --q6 --seed <N> --render`，Bonus 模式 `python tools/run_seeds.py --bonus`。

## 5. 仓库结构（哪些能改）

| 路径 | 说明 | 能否修改 |
|---|---|---|
| `src/main/__init__.py` | 你的全部作业（TODO 所在） | ✅ |
| `README.md` | 仅末尾两个"你来写"小节 | ✅ |
| `题面.pdf` | 题面（唯一规格说明） | ❌ 勿改 |
| `src/main/legacy_patrol.py` | Q7 模块（与主体同步发布，修复其缺陷） | Q7 时 ✅ |
| `.pre-commit-config.yaml` | AI 会话归档钩子配置 | ❌ 勿改 |
| `src/tests/`、`tools/`、`.github/`、`conftest.py`、`pytest.ini`、`main.py` | 测试与基础设施 | ❌ 勿改 |

CI 只允许修改 `src/main/**`、`README.md` 与 `.agent-sessions/**`（AI 会话归档）——其余文件改了直接红；autopep8 `--diff` 非空即败。提交方式（push、问卷、commit 粒度）见题面"提交与验收"一节。

## 6. Q3–Q6 实现说明

### Q3 SentryGrid 物理规则

实现 `SentryGrid` 的四个方法：

1. **`current_pos` setter**：三重输入校验——必须是长度为 2 的序列、元素为 int、坐标在网格范围内，否则抛 `ValueError`。
2. **`move_forward`**：先检查电量是否耗尽（`battery == 0` 抛错），再计算目标格；若越界或撞障碍则不耗电、原位不动、返回原朝向；否则移动一格、耗电 1、返回当前朝向。
3. **`turn_left` / `turn_right`**：按 `[UP, LEFT, DOWN, RIGHT]`（左转）和 `[UP, RIGHT, DOWN, LEFT]`（右转）顺序循环切换朝向，不耗电。

### Q4 贪心寻路 `next_step_toward`

1. **主轴选择**：水平距离 ≥ 垂直距离时优先水平方向，否则优先垂直方向。
2. **障碍判定**：跳过被障碍物占据或越界的候选方向；全部候选阻塞时回退到 `current_facing`。
3. **y 轴映射**：世界坐标 y 向上增长，垂直方向用 `Facing.UP`（y+）和 `Facing.DOWN`（y-）。

### Q5 决策 `decide`

按规则表 R1–R7 实现状态机：

1. **输入校验**：`sensor` 非 dict 或血量/距离/可见性字段缺失/类型错误时返回 `("RETREAT", SentryState.RETREAT)`。
2. **低血量优先**：血量百分比 ≤ 20% 时无条件 `RETREAT`，覆盖所有状态。
3. **状态转换**：`PATROL`（无敌人则原地 SCAN）→ `SUSPECT`（敌人可见但 >5m）→ `ENGAGE`（敌人可见且 ≤5m）→ `RETREAT`（血量 ≤ 20% 或弹药耗尽）→ `RETURN`（回到出生点后恢复 PATROL）。

### Q6 巡逻主循环

1. **`run_patrol`**：sense-decide-act 主循环，统计步数、SCAN/SHOOT/RETREAT 次数；`SCAN` 与 `SHOOT` 时向敌人方向移动一格以接近目标；最大步数限制防止死循环。
2. **`report_to_json`**：用 `json.dumps(stats, sort_keys=True, ensure_ascii=False)` 序列化统计结果，保证输出确定性。
3. **`bfs_path_length`**：BFS 求从起点到目标的最短步数，起点或终点在障碍物上时返回 -1。

## 7. Q7 遗留模块缺陷修复说明

`src/main/legacy_patrol.py` 共修复 6 处 bug：

1. **`total_route_meters` 单位换算错误**：`segment_length_cm` 返回厘米，但函数直接累加后未除以 100，导致返回值单位仍是厘米。修复：`return distance_in_meters / 100`。
2. **`calibrate` 未处理 `baseline` 为 `None`**：当样本中没有正数时，`first_positive` 返回 `None`，随后 `s - baseline` 抛出 `TypeError`。修复：`baseline is None` 时直接返回 0。
3. **`summarize_events` 比较运算符错误**：契约要求"id 不超过 max_id"，原代码用 `e["id"] < max_id`，漏掉了 id 等于 max_id 的事件。修复：改为 `e["id"] <= max_id`。
4. **`log` 可变默认参数**：`history=[]` 在函数定义时创建一次，多次调用会共享同一个列表。修复：改为 `history=None`，函数内判空初始化。
5. **`run_legacy_sim` 缺少循环自增**：`while` 循环内 `round_` 从未递增，导致死循环。修复：在循环末尾添加 `round_ += 1`。
6. **`run_legacy_sim` 终止条件反转**：契约要求体力 `<= 20` 时终止，原代码写的是 `if stamina > 20: break`，逻辑完全相反。修复：改为 `if stamina <= 20: break`。

