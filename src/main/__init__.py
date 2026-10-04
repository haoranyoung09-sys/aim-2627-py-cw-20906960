# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。

你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    """TODO(Q1)：血量百分比，返回 0-100 的 int；计算与边界规则见题面 Q1 规范。"""
    # raise NotImplementedError("Q1 hp_ratio：题面 Q1·血量百分比与精度保障")
    if max_hp <= 0:
        return 0
    if hp < 0:
        return 0
    if hp > max_hp:
        return 100
    hpratio = int((hp / max_hp) * 100)
    return hpratio


def status_report(name, robot_type, hp, max_hp, battery):
    """TODO(Q1)：一行自检报告字符串；档位判定与逐字符格式见题面 Q1 规范。"""
    # raise NotImplementedError("Q1 status_report：题面 Q1·电量映射与报告格式")
    hpratio = hp_ratio(hp, max_hp)
    # 电量档位：>=50 OK, >=20 WARNING, <20 LOW
    if battery >= 50:
        battery_status = "OK"
    elif battery >= 20:
        battery_status = "WARNING"
    else:
        battery_status = "LOW"

    return (f"{name:<10}|{robot_type:^10}"
            f"|HP {hpratio:>3}%|BAT {battery:>3}%|{battery_status}")


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
def analyze_damage_log(lines):
    """TODO(Q2)：解析混合格式伤害日志，返回固定契约的统计 dict；
    行格式、去重与统计口径见题面 Q2 规范。"""
    # raise NotImplementedError("Q2 analyze_damage_log：题面 Q2·多源日志解析与统计")
    ARMOR_MAP = {"F": "front", "L": "left", "R": "right"}
    VALID_ARMORS = {"front", "left", "right"}

    by_armor = {"front": 0, "left": 0, "right": 0}
    total = 0
    count = 0
    seen_ids = set()

    for raw in lines:
        try:
            line = raw.strip() if isinstance(raw, str) else None
            if not line or line.startswith("#"):
                continue

            # 尝试 JSON 行
            if line.startswith("{"):
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    continue
                armor = obj.get("armor")
                damage = obj.get("damage")
                if armor not in VALID_ARMORS:
                    continue
                if (not isinstance(damage, int) or isinstance(damage, bool)
                        or damage <= 0):
                    continue
                event_id = obj.get("id", None)
                if event_id is not None:
                    if event_id in seen_ids:
                        continue
                    seen_ids.add(event_id)
                by_armor[armor] += damage
                total += damage
                count += 1
                continue

            # 尝试传感器行 "F:32,L:5,R:12"
            segments = line.split(",")
            parsed = {}
            ok = True
            for seg in segments:
                seg = seg.strip()
                if ":" not in seg:
                    ok = False
                    break
                letter, _, num_str = seg.partition(":")
                letter = letter.strip()
                num_str = num_str.strip()
                if letter not in ARMOR_MAP:
                    ok = False
                    break
                try:
                    val = int(num_str)
                except (TypeError, ValueError):
                    ok = False
                    break
                if val <= 0:
                    ok = False
                    break
                if letter in parsed:  # 同字母重复出现视为脏行
                    ok = False
                    break
                parsed[letter] = val
            if not ok or not parsed:
                continue
            for letter, val in parsed.items():
                armor = ARMOR_MAP[letter]
                by_armor[armor] += val
                total += val
                count += 1
        except (ValueError, TypeError, KeyError):
            continue

    if count == 0:
        most_hit = None
        avg = 0.0
    else:
        # most_hit 取累计伤害最高的装甲面；全为 0 则为 None
        most_hit = max(by_armor, key=lambda a: by_armor[a])
        if by_armor[most_hit] == 0:
            most_hit = None
        avg = round(total / count, 2)

    return {"total": total, "by_armor": by_armor,
            "most_hit": most_hit, "avg": avg}


# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------
class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self._pos = self._clamp_cell(start_pos)
        if self._pos in self._obstacles:
            raise ValueError("start_pos 不能位于障碍物上")

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        """TODO(Q3)：位置 setter；三重输入校验见题面 Q3 规范第 1 条。"""
        # raise NotImplementedError("Q3 current_pos.setter：题面 Q3·位置校验三步")
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError("value 需要长度为 2 的 tuple/list")
        x, y = int(value[0]), int(value[1])
        if not (0 <= x < self._width and 0 <= y < self._height):
            raise IndexError("位置越界")
        if (x, y) in self._obstacles:
            raise ValueError("位置在障碍物上")
        self._pos = (x, y)

    def move_forward(self):
        """TODO(Q3)：朝当前 facing 前进一格，返回执行后的位置；
        碰撞、耗电与断电语义见题面 Q3 规范。"""
        # raise NotImplementedError("Q3 move_forward：题面 Q3·前进、碰撞与断电")
        # 电量耗尽时无论目标格是否可通行均抛错；碰撞不耗电、原位不动。
        if self._fuel <= 0:
            raise RuntimeError("电量耗尽，无法前进")
        dx, dy = self._facing.value
        nx = self._pos[0] + dx
        ny = self._pos[1] + dy
        if self.is_blocked(nx, ny):
            self._collision_count += 1
            return self._pos
        self._fuel -= 1
        self._pos = (nx, ny)
        return self._pos

    def turn_left(self):
        """TODO(Q3)：原地左转 90°，返回新的 Facing（不耗电）。"""
        # raise NotImplementedError("Q3 turn_left")
        order = [Facing.UP, Facing.LEFT, Facing.DOWN, Facing.RIGHT]
        idx = order.index(self._facing)
        self._facing = order[(idx + 1) % 4]
        return self._facing

    def turn_right(self):
        """TODO(Q3)：原地右转 90°，返回新的 Facing（不耗电）。"""
        # raise NotImplementedError("Q3 turn_right")
        order = [Facing.UP, Facing.RIGHT, Facing.DOWN, Facing.LEFT]
        idx = order.index(self._facing)
        self._facing = order[(idx + 1) % 4]
        return self._facing


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    """TODO(Q4)：返回下一步应朝向的 Facing；
    候选判定、优先级与回退规则见题面 Q4 规范。"""
    # raise NotImplementedError("Q4 next_step_toward：题面 Q4·贪心策略与回退")
    px, py = pos
    tx, ty = target
    dx = tx - px
    dy = ty - py

    # 主轴：水平差 >= 垂直差时优先水平，否则优先垂直
    horiz_first = abs(dx) >= abs(dy)

    primary = []
    secondary = []
    if horiz_first:
        if dx > 0:
            primary.append(Facing.RIGHT)
        elif dx < 0:
            primary.append(Facing.LEFT)
        if dy > 0:
            secondary.append(Facing.UP)
        elif dy < 0:
            secondary.append(Facing.DOWN)
    else:
        if dy > 0:
            primary.append(Facing.UP)
        elif dy < 0:
            primary.append(Facing.DOWN)
        if dx > 0:
            secondary.append(Facing.RIGHT)
        elif dx < 0:
            secondary.append(Facing.LEFT)

    # 障碍判定：跳过被障碍物占据的候选方向；全部阻塞则回退到 current_facing
    obstacle_set = set(obstacles) if obstacles else set()
    for cand in primary + secondary:
        cdx, cdy = cand.value
        nxt = (px + cdx, py + cdy)
        if nxt not in obstacle_set:
            return cand
    return current_facing


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------
class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


def decide(sensor, state, hp, heat):
    """TODO(Q5)：纯函数决策，返回 (action: str, new_state: SentryState)；
    sensor 字段契约、R1-R7 规则表与非法输入处理见题面 Q5 规范。"""
    # raise NotImplementedError("Q5 decide：题面 Q5·决策规则表 R1-R7")
    # ---- 输入契约校验 ----
    if not isinstance(sensor, dict):
        raise ValueError("sensor 必须为 dict")
    frames = sensor.get("enemy_frames")
    if (not isinstance(frames, (list, tuple)) or len(frames) == 0
            or not all(isinstance(f, bool) for f in frames)):
        raise ValueError("enemy_frames 必须是非空 bool 序列")
    if not isinstance(state, SentryState):
        raise ValueError("state 必须为 SentryState")
    max_hp = sensor.get("max_hp", 100)

    enemy_seen = any(frames)
    two_frames = len(frames) >= 2 and frames[-1] and frames[-2]

    # 低血量（≤20%）最高优先级：直接撤退，覆盖所有状态
    ratio = hp_ratio(hp, max_hp)
    if ratio <= 20:
        return ("RETREAT", SentryState.RETREAT)

    # Q5 commit 2: ENGAGE/RETREAT/RETURN
    if state == SentryState.PATROL:
        if enemy_seen:
            return ("SCAN", SentryState.SUSPECT)
        return ("PATROL_MOVE", SentryState.PATROL)
    elif state == SentryState.SUSPECT:
        if two_frames:
            return ("SHOOT", SentryState.ENGAGE)
        if enemy_seen:
            return ("SCAN", SentryState.SUSPECT)
        return ("PATROL_MOVE", SentryState.PATROL)
    elif state == SentryState.ENGAGE:
        if enemy_seen:
            return ("SHOOT", SentryState.ENGAGE)
        return ("SCAN", SentryState.SUSPECT)
    elif state == SentryState.RETREAT:
        if not enemy_seen:
            return ("RETURN", SentryState.RETURN)
        return ("RETREAT", SentryState.RETREAT)
    elif state == SentryState.RETURN:
        return ("MOVE_BASE", SentryState.PATROL)
    return ("PATROL_MOVE", SentryState.PATROL)


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def run_patrol(grid, max_steps=500):
    """TODO(Q6)：sense → decide → act 主循环；
    循环结构、终止条件、脱困自由度与统计返回契约见题面 Q6 规范。"""
    # raise NotImplementedError("Q6 run_patrol：题面 Q6·主循环与统计契约")
    start_pos = grid.current_pos
    state = SentryState.PATROL
    hp = 100
    max_hp = 100
    heat = 0
    collisions = 0
    steps = 0
    enemy_frames = []

    for step in range(max_steps):
        steps = step + 1
        # ---- sense ----
        px, py = grid.current_pos
        ex, ey = grid.enemy_pos
        dist = abs(px - ex) + abs(py - ey)
        in_range = dist <= 4
        enemy_frames.append(in_range)
        if len(enemy_frames) > 3:
            enemy_frames.pop(0)
        sensor = {
            "enemy_frames": tuple(enemy_frames),
            "enemy_dist": dist if in_range else None,
            "robot_type": "INFANTRY",
            "max_hp": max_hp,
        }

        # ---- decide ----
        action, state = decide(sensor, state, hp, heat)

        # ---- act ----
        if action == "PATROL_MOVE":
            direction = next_step_toward(
                grid.current_pos, grid.enemy_pos, grid.obstacles, grid.facing)
            _face_and_move(grid, direction)
        elif action == "SCAN":
            direction = next_step_toward(
                grid.current_pos, grid.enemy_pos, grid.obstacles, grid.facing)
            _face_and_move(grid, direction)
        elif action == "SHOOT":
            direction = next_step_toward(
                grid.current_pos, grid.enemy_pos, grid.obstacles, grid.facing)
            _face_and_move(grid, direction)
        elif action == "RETREAT":
            # 向远离敌人的方向移动
            direction = _retreat_direction(grid)
            _face_and_move(grid, direction)
        elif action in ("RETURN", "MOVE_BASE"):
            direction = next_step_toward(
                grid.current_pos, start_pos, grid.obstacles, grid.facing)
            _face_and_move(grid, direction)

        collisions = grid.collision_count
        if grid.found_enemy:
            return {"success": True, "steps": steps,
                    "collisions": collisions, "state": state.value}

    return {"success": grid.found_enemy, "steps": steps,
            "collisions": collisions, "state": state.value}


def _turn_to(grid, direction):
    """原地转向到目标方向（最多 3 次 turn_left/right）。"""
    order_cw = [Facing.UP, Facing.RIGHT, Facing.DOWN, Facing.LEFT]
    cur = order_cw.index(grid.facing)
    tgt = order_cw.index(direction)
    diff = (tgt - cur) % 4
    if diff == 0:
        return
    if diff <= 2:
        for _ in range(diff):
            grid.turn_right()
    else:
        for _ in range(4 - diff):
            grid.turn_left()


def _face_and_move(grid, direction):
    """转向并前进一格。"""
    _turn_to(grid, direction)
    grid.move_forward()


def _retreat_direction(grid):
    """选择远离敌人且不被阻挡的方向。"""
    px, py = grid.current_pos
    ex, ey = grid.enemy_pos
    dx = px - ex
    dy = py - ey
    horiz_first = abs(dx) >= abs(dy)
    cands = []
    if horiz_first:
        if dx > 0:
            cands.append(Facing.RIGHT)
        elif dx < 0:
            cands.append(Facing.LEFT)
        if dy > 0:
            cands.append(Facing.UP)
        elif dy < 0:
            cands.append(Facing.DOWN)
    else:
        if dy > 0:
            cands.append(Facing.UP)
        elif dy < 0:
            cands.append(Facing.DOWN)
        if dx > 0:
            cands.append(Facing.RIGHT)
        elif dx < 0:
            cands.append(Facing.LEFT)
    obs = grid.obstacles
    for c in cands:
        cdx, cdy = c.value
        nxt = (px + cdx, py + cdy)
        if nxt not in obs and 0 <= nxt[0] < grid.width and 0 <= nxt[1] < grid.height:
            return c
    return grid.facing


def report_to_json(stats):
    """TODO(Q6)：把 stats 序列化为确定性的 JSON 字符串，见题面 Q6 规范。"""
    # raise NotImplementedError("Q6 report_to_json：题面 Q6·报告序列化")
    return json.dumps(stats, sort_keys=True, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    """TODO(Bonus)：BFS 全局最短路步数；返回语义与边界职责见题面 Bonus 规范。"""
    # raise NotImplementedError("Bonus bfs_path_length")
    start = (int(start[0]), int(start[1]))
    target = (int(target[0]), int(target[1]))
    if start == target:
        return 0
    obs = set()
    for ob in obstacles:
        obs.add((int(ob[0]), int(ob[1])))
    if target in obs or start in obs:
        return -1
    from collections import deque
    visited = {start}
    queue = deque([(start, 0)])
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    while queue:
        (x, y), d = queue.popleft()
        for dx, dy in dirs:
            nxt = (x + dx, y + dy)
            if nxt == target:
                return d + 1
            if nxt in obs or nxt in visited:
                continue
            visited.add(nxt)
            queue.append((nxt, d + 1))
    return -1


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
