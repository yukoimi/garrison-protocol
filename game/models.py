"""卫戍协议 - 数据模型"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import random
import uuid


class TraitType(Enum):
    COMBAT = "作战能力"
    PREP = "整备能力"
    STACK_CONTINUOUS = "持续叠加"
    STACK_SINGLE = "单次叠加"
    SPECIAL = "特异化"


class TriggerType(Enum):
    ON_OBTAIN = "获得时"
    ON_DEPLOY = "部署时"
    ON_SELL = "售出时"
    ON_DEFEAT = "被击倒时"
    ON_REST_START = "进入休整期时"
    ON_REST_END = "休整期结束时"
    IN_COMBAT = "战斗中"
    ON_COMBAT_START = "战斗开始时"
    ON_REFRESH = "刷新时"
    ON_SKILL = "开启技能时"


@dataclass
class PactEffect:
    """盟约效果的定义"""
    base: float          # 基础值
    coeff: float         # 每层系数
    cap: float           # 上限
    description: str     # 效果描述模板


@dataclass
class Pact:
    """盟约"""
    id: str
    name: str
    is_core: bool           # 核心盟约 or 附加盟约
    activate_count: int     # 激活所需人数
    advanced_count: int     # 进阶效果所需人数
    effect_desc: str        # 效果描述
    advanced_desc: str = "" # 进阶效果描述
    group: int = 0          # 关键目标组 (1-6)


@dataclass
class Trait:
    """干员特质"""
    trait_type: TraitType
    trigger: TriggerType           # 触发条件
    target_pact: Optional[str]     # 目标盟约ID (None = 自身所有盟约)
    stack_amount: int = 1          # 层数增加量
    elite_stack_amount: int = 2    # 精锐状态层数增加量
    description: str = ""


@dataclass
class Operator:
    """干员"""
    id: str
    name: str
    tier: int                      # 等阶 Ⅰ~Ⅵ (1~6)
    cost: int                      # 购买费用
    pacts: list                    # 盟约ID列表
    traits: list                   # 特质列表
    is_elite: bool = False         # 精锐状态
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])  # 实例唯一标识
    base_hp: int = 1000
    base_atk: int = 300
    base_def: int = 100
    base_res: int = 0
    atk_speed: float = 1.0         # 攻击间隔(秒)
    block_count: int = 0
    deploy_cost: int = 10
    redeploy_time: int = 12
    healer: bool = False  # 奶妈标记

    @property
    def hp(self) -> int:
        return int(self.base_hp * (1.15 if self.is_elite else 1.0))

    @property
    def atk(self) -> int:
        return int(self.base_atk * (1.15 if self.is_elite else 1.0))

    @property
    def defense(self) -> int:
        return int(self.base_def * (1.15 if self.is_elite else 1.0))


@dataclass
class BattleOperator:
    """战场上部署的干员"""
    operator: Operator
    hp: int
    max_hp: int
    atk: int
    defense: int
    attack_timer: float = 0.0
    target: Optional['Enemy'] = None
    is_deployed: bool = True

    def take_damage(self, raw_dmg: int) -> int:
        actual = max(int(raw_dmg * 0.05), raw_dmg - self.defense)
        self.hp -= actual
        return actual


@dataclass
class Enemy:
    """敌人"""
    id: str
    name: str
    hp: int
    max_hp: int
    atk: int
    defense: int
    speed: float         # 移动速度 (格/秒)
    is_elite: bool = False
    is_boss: bool = False
    position: float = 0.0   # 当前位置 (0=入口, 10=基地)
    attack_timer: float = 0.0
    target: Optional[BattleOperator] = None
    blocked_by: Optional[BattleOperator] = None

    def take_damage(self, raw_dmg: int, is_arts: bool = False) -> int:
        if is_arts:
            actual = max(int(raw_dmg * 0.05), int(raw_dmg * (1 - 0)))
        else:
            actual = max(int(raw_dmg * 0.05), raw_dmg - self.defense)
        self.hp -= actual
        return actual


@dataclass
class Strategy:
    """策略报告"""
    id: str
    name: str
    initiator: str
    hp: int
    effect_desc: str
    unlock_condition: str = "初始"


@dataclass
class Equipment:
    """战略装备"""
    id: str
    name: str
    tier: int
    cost: int
    effect_desc: str


@dataclass
class PactState:
    """盟约运行时状态"""
    pact: Pact
    layers: int = 0             # 当前层数
    active: bool = False        # 是否已激活
    advanced_active: bool = False  # 进阶是否激活
    operator_count: int = 0     # 场上该盟约干员数


@dataclass
class WaveConfig:
    """波次配置"""
    wave_num: int
    enemies: list  # list of (enemy_id, count)


# ============================================================
# 塔防地图模型
# ============================================================

class TileType(Enum):
    GROUND = "ground"     # 地面（可部署近战）
    RANGED = "ranged"     # 高台（可部署远程）
    ROAD = "road"         # 敌人路径
    BLOCKED = "blocked"   # 不可部署
    SPAWN = "spawn"       # 敌人出生点
    GOAL = "goal"         # 防守目标点


@dataclass
class GridCell:
    """地图格子"""
    x: int
    y: int
    tile_type: TileType = TileType.BLOCKED
    occupied: bool = False
    can_deploy: bool = False

    @property
    def color(self) -> tuple:
        if self.occupied:
            return (100, 100, 180)
        return {
            TileType.GROUND: (60, 130, 60),
            TileType.RANGED: (160, 140, 60),
            TileType.ROAD: (80, 80, 80),
            TileType.BLOCKED: (40, 40, 40),
            TileType.SPAWN: (180, 40, 40),
            TileType.GOAL: (40, 40, 180),
        }.get(self.tile_type, (40, 40, 40))


@dataclass
class GameMap:
    """游戏地图"""
    width: int
    height: int
    cells: List[List[GridCell]] = field(default_factory=list)
    spawn_points: List[tuple] = field(default_factory=list)
    goal_points: List[tuple] = field(default_factory=list)

    def __post_init__(self):
        if not self.cells:
            self.cells = [[GridCell(x, y) for y in range(self.height)] for x in range(self.width)]

    def get_cell(self, x: int, y: int) -> Optional[GridCell]:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[x][y]
        return None

    def get_spawn_cell(self) -> Optional[tuple]:
        if self.spawn_points:
            return random.choice(self.spawn_points)
        return None

    def is_valid_deploy(self, x: int, y: int, is_melee: bool) -> bool:
        cell = self.get_cell(x, y)
        if not cell or not cell.can_deploy or cell.occupied:
            return False
        if is_melee and cell.tile_type != TileType.GROUND:
            return False
        if not is_melee and cell.tile_type != TileType.RANGED:
            return False
        return True


def create_default_map() -> GameMap:
    """创建默认地图: 12列 x 7行, 标准塔防布局"""
    game_map = GameMap(width=12, height=7)

    for x in range(12):
        for y in range(7):
            cell = GridCell(x=x, y=y)
            # 第2行和第4行是道路
            if y in (2, 4):
                cell.tile_type = TileType.ROAD
            elif y in (1, 5):
                cell.tile_type = TileType.GROUND
                cell.can_deploy = True
            elif y in (0, 6):
                cell.tile_type = TileType.RANGED
                cell.can_deploy = True
            elif y == 3:
                cell.tile_type = TileType.RANGED
                cell.can_deploy = True
            game_map.cells[x][y] = cell

    # 出生点(右侧)
    for y in (2, 4):
        cell = game_map.cells[11][y]
        cell.tile_type = TileType.SPAWN
        cell.can_deploy = False
        game_map.spawn_points.append((11, y))

    # 目标点(左侧)
    for y in (2, 4):
        cell = game_map.cells[0][y]
        cell.tile_type = TileType.GOAL
        cell.can_deploy = False
        game_map.goal_points.append((0, y))

    return game_map
