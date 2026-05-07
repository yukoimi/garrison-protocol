"""卫戍协议 - 战斗引擎"""
import random
import math
from typing import Optional
from dataclasses import dataclass, field

from .models import (
    Operator, BattleOperator, Enemy, PactState, Pact, WaveConfig,
    TraitType, TriggerType,
)
from .data import (
    ALL_PACTS, CORE_PACTS, EXTRA_PACTS,
    OPERATORS, ENEMIES, generate_waves, calc_pact_effect,
)


@dataclass
class BattleResult:
    """单场战斗结果"""
    won: bool
    enemies_killed: int
    enemies_total: int
    operators_lost: int
    damage_dealt: int
    damage_taken: int
    is_perfect: bool   # 完美作战 (无漏怪)


@dataclass
class GameState:
    """全局游戏状态"""
    round_num: int = 0
    funds: int = 0
    total_funds_earned: int = 0
    life: int = 20
    max_operators: int = 10
    shop_size: int = 5
    refresh_cost: int = 2
    free_refreshes: int = 0
    difficulty: str = "标准"

    # 干员
    roster: list = field(default_factory=list)      # 已购买的干员
    deployed: list = field(default_factory=list)     # 战场上部署的干员 (BattleOperator)
    bench: list = field(default_factory=list)        # 整备区的干员 (未部署)

    # 盟约状态
    pact_states: dict = field(default_factory=dict)  # pact_id -> PactState

    # 策略
    strategy: 'Strategy | None' = None
    free_refreshes: int = 0  # 普罗旺斯等给予的免费刷新次数

    # 波次
    current_wave: int = 0
    total_waves: int = 15

    # 战斗历史
    results: list = field(default_factory=list)

    def __post_init__(self):
        for pid, pact in ALL_PACTS.items():
            self.pact_states[pid] = PactState(pact=pact)

    @property
    def available_deploy_slots(self) -> int:
        return self.max_operators - len(self.deployed)


class BattleEngine:
    """战斗模拟引擎"""

    TRACK_LENGTH = 10.0     # 战场长度 (格)
    TICK_DURATION = 0.5     # 每tick秒数
    MAX_BATTLE_TICKS = 600  # 最大tick数 (300秒)

    def __init__(self, state: GameState):
        self.state = state
        self.enemies: list[Enemy] = []
        self.battle_ops: list[BattleOperator] = []
        self.tick_count = 0
        self.leaked = 0
        self.killed = 0
        self.total_dmg_dealt = 0
        self.total_dmg_taken = 0
        self.log: list[str] = []

    def _log(self, msg: str):
        self.log.append(msg)

    def setup_battle(self, wave_cfg: WaveConfig, diff_mult: float):
        """初始化战斗"""
        self.enemies.clear()
        self.battle_ops.clear()
        self.tick_count = 0
        self.leaked = 0
        self.killed = 0
        self.log.clear()

        # 部署所有在deployed中的干员
        for op in self.state.deployed:
            bo = BattleOperator(
                operator=op,
                hp=op.hp, max_hp=op.hp,
                atk=op.atk, defense=op.defense,
                attack_timer=random.uniform(0, op.atk_speed * 0.5),
            )
            self.battle_ops.append(bo)

        # 生成敌人
        for enemy_id, count in wave_cfg.enemies:
            template = ENEMIES.get(enemy_id)
            if not template:
                continue
            for _ in range(count):
                e = Enemy(
                    id=template.id, name=template.name,
                    hp=int(template.hp * diff_mult),
                    max_hp=int(template.max_hp * diff_mult),
                    atk=int(template.atk * diff_mult),
                    defense=int(template.defense * diff_mult),
                    speed=template.speed,
                    is_elite=template.is_elite,
                    is_boss=template.is_boss,
                    position=0.0,
                )
                self.enemies.append(e)

        # 按速度排序(快的在前面)
        self.enemies.sort(key=lambda e: -e.speed)

        self._log(f"=== 第{wave_cfg.wave_num}波 开始 ===")
        self._log(f"敌人数量: {len(self.enemies)}, 部署干员: {len(self.battle_ops)}")

    def _get_pact_bonus(self, pact_id: str, base_val: float) -> float:
        """获取盟约加成"""
        ps = self.state.pact_states.get(pact_id)
        if not ps or not ps.active:
            return 1.0
        effect = calc_pact_effect(pact_id, ps.layers)
        return 1.0 + effect / 100.0

    def _apply_pact_buffs(self, op: BattleOperator):
        """对干员应用盟约加成"""
        atk_mult = 1.0
        hp_mult = 1.0
        def_mult = 1.0
        aspd_bonus = 0.0

        for pid, ps in self.state.pact_states.items():
            if not ps.active:
                continue
            layers = ps.layers

            if pid == "yan":
                atk_mult *= 1.0 + (23 + 0.9 * layers) / 100.0
            elif pid == "kazimierz":
                atk_mult *= 1.0 + (50 + 1.0 * layers) / 100.0
            elif pid == "aegir":
                hp_mult *= 1.0 + (35 + 1.0 * layers) / 100.0
                atk_mult *= 1.0 + (35 + layers) * 0.75 / 100.0
            elif pid == "precision":
                atk_mult *= 1.0 + (10 + 1.2 * layers) / 100.0
            elif pid == "assault":
                atk_mult *= 1.0 + (25 + 1.0 * layers) / 100.0
                hp_mult *= 1.0 + (25 + 1.0 * layers) / 100.0
            elif pid == "solo":
                solo_count = sum(1 for o in self.battle_ops if "solo" in o.operator.pacts)
                if solo_count <= 1:
                    atk_mult *= 1.6
                    hp_mult *= 1.6
            elif pid == "fortification":
                hp_mult *= 1.0 + (25 + 1.2 * layers) / 100.0
            elif pid == "assistance":
                def_mult *= 1.0 + (15 + 1.2 * layers) / 100.0
            elif pid == "agility":
                aspd_bonus += 10 + 1.0 * layers
            elif pid == "assault" and layers >= 50:
                aspd_bonus += 50
            elif pid == "kjerag":
                atk_mult *= 1.25
            elif pid == "victoria":
                atk_mult *= 1.0 + (125 + 0.8 * layers - 100) / 100.0
            elif pid == "siracusa":
                aspd_bonus += 25 + 0.8 * layers
            elif pid == "arcane":
                atk_mult *= 1.0 + (20 + layers) / 100.0
            elif pid == "joint_defense":
                pass  # 减伤在受伤时处理

        op.max_hp = int(op.operator.hp * hp_mult)
        op.hp = min(op.hp, op.max_hp)
        op.atk = int(op.operator.atk * atk_mult)
        op.defense = int(op.operator.defense * def_mult)
        op.operator.atk_speed = max(0.3, op.operator.atk_speed * (100 / (100 + max(0, aspd_bonus))))

    def tick(self) -> bool:
        """执行一个tick, 返回True如果战斗继续"""
        self.tick_count += 1

        # 1. 检查战斗是否结束
        if not self.enemies and self.tick_count > 1:
            return False
        if not self.battle_ops and self.enemies:
            # 所有干员被击倒
            for e in self.enemies:
                if e.position >= self.TRACK_LENGTH:
                    self.leaked += 1
            return False

        # 2. 敌人移动
        for enemy in self.enemies[:]:
            if enemy.position >= self.TRACK_LENGTH:
                self.leaked += 1
                self.enemies.remove(enemy)
                self._log(f"  ⚠ {enemy.name} 突破防线!")
                continue

            if enemy.blocked_by and enemy.blocked_by.hp > 0:
                continue

            enemy.blocked_by = None
            enemy.position += enemy.speed * self.TICK_DURATION

            # 检查是否被阻挡
            for bo in self.battle_ops:
                if bo.hp <= 0:
                    continue
                # 简化: block范围内的干员阻挡敌人
                if enemy.position >= self.TRACK_LENGTH * 0.7:
                    enemy.blocked_by = bo
                    enemy.position = self.TRACK_LENGTH * 0.7
                    break

        # 3. 干员攻击
        for bo in self.battle_ops[:]:
            if bo.hp <= 0:
                self.battle_ops.remove(bo)
                continue

            bo.attack_timer -= self.TICK_DURATION
            if bo.attack_timer > 0:
                continue

            # 找目标
            target = None
            min_dist = float('inf')
            for enemy in self.enemies:
                dist = abs(enemy.position - self.TRACK_LENGTH * 0.7)
                if dist < min_dist:
                    min_dist = dist
                    target = enemy

            if target:
                bo.attack_timer = bo.operator.atk_speed
                # 物理伤害
                dmg = max(int(bo.atk * 0.05), bo.atk - target.defense)
                actual = target.take_damage(dmg)
                self.total_dmg_dealt += actual

                if target.hp <= 0:
                    self.killed += 1
                    self.enemies.remove(target)
                    self._log(f"  ✓ {bo.operator.name} 击杀 {target.name}")
                else:
                    if self.tick_count <= 3:
                        self._log(f"  {bo.operator.name} → {target.name} ({actual}伤害, 剩余{target.hp}HP)")

        # 4. 敌人攻击被阻挡者
        for enemy in self.enemies:
            if enemy.blocked_by and enemy.blocked_by.hp > 0:
                enemy.attack_timer -= self.TICK_DURATION
                if enemy.attack_timer <= 0:
                    enemy.attack_timer = 1.5
                    dmg = enemy.atk
                    actual = enemy.blocked_by.take_damage(dmg)
                    self.total_dmg_taken += actual
                    if enemy.blocked_by.hp <= 0:
                        self._log(f"  ✗ {enemy.blocked_by.operator.name} 被 {enemy.name} 击倒!")

        # 5. 检查超时
        if self.tick_count >= self.MAX_BATTLE_TICKS:
            # 强制结束, 剩余敌人全部漏掉
            for e in self.enemies:
                self.leaked += 1
            self.enemies.clear()
            return False

        return True

    def run(self, wave_cfg: WaveConfig, diff_mult: float) -> BattleResult:
        """运行一场完整战斗"""
        self.setup_battle(wave_cfg, diff_mult)

        # Apply pact buffs
        for bo in self.battle_ops:
            self._apply_pact_buffs(bo)

        while self.tick():
            pass

        won = self.leaked == 0
        ops_lost = len(self.state.deployed) - len(self.battle_ops)

        total_enemies = sum(c for _, c in wave_cfg.enemies)
        result = BattleResult(
            won=won,
            enemies_killed=self.killed,
            enemies_total=total_enemies,
            operators_lost=ops_lost,
            damage_dealt=self.total_dmg_dealt,
            damage_taken=self.total_dmg_taken,
            is_perfect=(self.leaked == 0),
        )
        return result


class PactLayerEngine:
    """盟约层数计算引擎"""

    @staticmethod
    def update_activation(state: GameState):
        """更新盟约激活状态(根据场上部署+整备区干员)"""
        pact_counts = {}
        for op in state.deployed:
            seen = set()
            for pid in op.pacts:
                if pid not in seen:
                    pact_counts[pid] = pact_counts.get(pid, 0) + 1
                    seen.add(pid)
        # 投资人和远见: 整备区也算
        for op in state.bench:
            for pid in op.pacts:
                if pid in ('investor', 'foresight'):
                    pact_counts[pid] = pact_counts.get(pid, 0) + 1

        # 检查调和效果
        harmony_count = pact_counts.get("harmony", 0)
        harmony_bonus = 1 if harmony_count > 0 else 0

        for pid, ps in state.pact_states.items():
            pact = ps.pact
            count = pact_counts.get(pid, 0)
            ps.operator_count = count

            required = max(1, pact.activate_count - (harmony_bonus if pact.is_core else 0))
            ps.active = count >= required

            if ps.active and pact.advanced_count:
                adv_required = max(1, pact.advanced_count - (harmony_bonus if pact.is_core else 0))
                ps.advanced_active = count >= adv_required

    @staticmethod
    def trigger_trait(state: GameState, trigger: TriggerType, operator=None, context: dict = None):
        """触发特质(在对应生命周期节点调用)"""
        context = context or {}
        layers_added = {}

        # 确定哪些干员的特质需要触发
        targets = []
        if operator and trigger in (TriggerType.ON_OBTAIN, TriggerType.ON_DEPLOY,
                                     TriggerType.ON_SELL, TriggerType.ON_DEFEAT):
            targets = [operator]
        elif trigger == TriggerType.ON_REST_START:
            targets = state.roster  # 所有干员(整备区+部署)
        elif trigger == TriggerType.ON_REST_END:
            targets = state.roster
        elif trigger == TriggerType.ON_COMBAT_START:
            targets = list(state.deployed)
        elif trigger == TriggerType.ON_REFRESH:
            targets = state.roster

        for op in targets:
            is_elite = op.is_elite
            for trait in op.traits:
                if trait.trigger != trigger:
                    continue

                amount = trait.elite_stack_amount if is_elite else trait.stack_amount
                if amount <= 0:
                    continue

                # 确定目标盟约
                pact_ids = trait.target_pact
                if pact_ids is None:
                    pact_ids = op.pacts

                if isinstance(pact_ids, str):
                    pact_ids = [pact_ids]

                for pid in pact_ids:
                    if pid not in ALL_PACTS:
                        continue
                    layers_added[pid] = layers_added.get(pid, 0) + amount

        # 应用层数
        for pid, amount in layers_added.items():
            if pid in state.pact_states:
                state.pact_states[pid].layers += amount

        return layers_added

    @staticmethod
    def trigger_rest_start(state: GameState):
        """休整期开始时触发"""
        return PactLayerEngine.trigger_trait(state, TriggerType.ON_REST_START)

    @staticmethod
    def trigger_rest_end(state: GameState):
        """休整期结束时触发"""
        return PactLayerEngine.trigger_trait(state, TriggerType.ON_REST_END)

    @staticmethod
    def trigger_deploy(state: GameState, operator):
        """部署干员时触发"""
        return PactLayerEngine.trigger_trait(state, TriggerType.ON_DEPLOY, operator)

    @staticmethod
    def trigger_obtain(state: GameState, operator):
        """获得干员时触发"""
        return PactLayerEngine.trigger_trait(state, TriggerType.ON_OBTAIN, operator)

    @staticmethod
    def trigger_defeat(state: GameState, operator):
        """干员被击倒时触发"""
        return PactLayerEngine.trigger_trait(state, TriggerType.ON_DEFEAT, operator)

    @staticmethod
    def trigger_refresh(state: GameState):
        """刷新时触发"""
        return PactLayerEngine.trigger_trait(state, TriggerType.ON_REFRESH)

    @staticmethod
    def trigger_combat_start(state: GameState):
        """战斗开始时触发"""
        return PactLayerEngine.trigger_trait(state, TriggerType.ON_COMBAT_START)


def get_shop_operators(state: GameState) -> list:
    """生成商店干员列表"""
    # 根据回合数调整等阶概率
    tier_weights = {
        1: max(10, 60 - state.round_num * 3),
        2: 25,
        3: min(12 + state.round_num * 2, 30),
        4: min(3 + state.round_num, 20),
        5: min(0 + max(0, state.round_num - 8) * 3, 15),
        6: min(0 + max(0, state.round_num - 12) * 5, 10),
    }

    shop = []
    for _ in range(state.shop_size):
        tier = random.choices(
            list(tier_weights.keys()),
            weights=list(tier_weights.values()),
            k=1
        )[0]
        candidates = [op for op in OPERATORS if op.tier == tier]
        if candidates:
            op = random.choice(candidates)
            shop.append(op)

    return shop


def get_round_funds(state: GameState) -> int:
    """计算回合资金"""
    base = 10 + state.round_num * 1.5

    # 远见加成
    foresight_ps = state.pact_states.get("foresight")
    if foresight_ps and foresight_ps.active:
        base += int(foresight_ps.layers / 10) * 2

    # 利息
    interest = min(5, int(state.funds / 10))
    base += interest

    return int(base)
