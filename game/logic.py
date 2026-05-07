"""卫戍协议 - 战斗逻辑 (独立于UI)"""
from .engine import PactLayerEngine
from .data import ALL_PACTS


class BattleLogic:

    @staticmethod
    def calc_atk_mult(state, op, b_ops):
        m = 1.0
        s = state.strategy
        if s and s.id == 's5':
            m *= 1.20
        elif s and s.id == 's2':
            n = sum(1 for ps in state.pact_states.values() if ps.active)
            if n >= 5:
                m *= 1.40
            elif n >= 4:
                m *= 1.30
            elif n >= 3:
                m *= 1.20
        for pid, ps in state.pact_states.items():
            if not ps.active:
                continue
            lyr = ps.layers
            has = pid in op.pacts
            if pid == 'yan' and has:
                m *= 1.0 + (23 + 0.9 * lyr) / 100.0
            elif pid == 'kazimierz' and has:
                m *= 1.0 + (50 + lyr) / 100.0
            elif pid == 'precision' and has:
                m *= 1.0 + (10 + 1.2 * lyr) / 100.0
            elif pid == 'assault' and has:
                m *= 1.0 + (25 + lyr) / 100.0
            elif pid == 'kjerag' and has:
                m *= 1.0 + 0.25 + 0.01 * lyr
            elif pid == 'victoria' and has:
                m *= 1.0 + 0.25 + 0.008 * lyr
            elif pid == 'sargon' and has:
                m *= 1.0 + (50 + lyr) / 100.0
            elif pid == 'siracusa' and has:
                m *= 1.0 + (15 + 0.4 * lyr) / 100.0
            elif pid == 'laterano' and has:
                m *= 1.0 + (20 + 0.5 * lyr) / 100.0
            elif pid == 'solo' and has:
                n = sum(1 for b in b_ops if b.get('alive', True) and 'solo' in b['op'].pacts)
                if n <= 1:
                    m *= 1.6
            elif pid == 'aegir' and has:
                m *= 1.0 + (35 + lyr) * 0.75 / 100.0
            elif pid == 'arcane' and has:
                m *= 1.0 + (20 + lyr) / 100.0
        m *= 1.0 + BattleLogic._get_trait_bonus(op, 'atk')
        return m

    @staticmethod
    def calc_hp_mult(state, op, b_ops):
        m = 1.0
        for pid, ps in state.pact_states.items():
            if not ps.active:
                continue
            lyr = ps.layers
            has = pid in op.pacts
            if pid == 'aegir' and has:
                m *= 1.0 + (35 + lyr) / 100.0
            elif pid == 'fortification' and has:
                m *= 1.0 + (25 + 1.2 * lyr) / 100.0
            elif pid == 'assault' and has:
                m *= 1.0 + (25 + lyr) / 100.0
            elif pid == 'solo' and has:
                n = sum(1 for b in b_ops if b.get('alive', True) and 'solo' in b['op'].pacts)
                if n <= 1:
                    m *= 1.6
            elif pid == 'yan' and has:
                m *= 1.0 + (23 + 0.9 * lyr) / 200.0
            elif pid == 'kazimierz' and has:
                m *= 1.0 + (50 + lyr) / 200.0
            elif pid == 'kjerag' and has:
                m *= 1.0 + 0.12 + 0.005 * lyr
            elif pid == 'victoria' and has:
                m *= 1.0 + 0.12 + 0.004 * lyr
            elif pid == 'sargon' and has:
                m *= 1.0 + (50 + lyr) / 200.0
            elif pid == 'precision' and has:
                m *= 1.0 + (10 + 1.2 * lyr) / 200.0
        m *= 1.0 + BattleLogic._get_trait_bonus(op, 'hp')
        return m

    @staticmethod
    def calc_def_mult(state, op):
        m = 1.0
        for pid, ps in state.pact_states.items():
            if not ps.active:
                continue
            if pid == 'assistance' and pid in op.pacts:
                m *= 1.0 + (15 + 1.2 * ps.layers) / 100.0
        # 特质加成
        m *= 1.0 + BattleLogic._get_trait_bonus(op, 'def')
        return m

    @staticmethod
    def _get_trait_bonus(op, stat):
        """解析特质描述, 返回atk/def/hp的百分比加成"""
        bonus = 0.0
        for t in op.traits:
            td = t.description
            if stat == 'def':
                if '自身防御+30%' in td: bonus = max(bonus, 0.30)
                if '防御+50%' in td: bonus = max(bonus, 0.50)
                if '防御+40%' in td: bonus = max(bonus, 0.40)
                if '攻防+30%' in td: bonus = max(bonus, 0.30)
                if '全属性+25%' in td: bonus = max(bonus, 0.25)
                if '防御+10%' in td: bonus = max(bonus, 0.10)
                if '全队防御+20%' in td: bonus = max(bonus, 0.20)
            elif stat == 'atk':
                if '自身攻击力+30%' in td: bonus = max(bonus, 0.30)
                if '攻击力额外+20%' in td: bonus = max(bonus, 0.20)
                if '攻击力额外+12%' in td: bonus = max(bonus, 0.12)
                if '攻防+30%' in td: bonus = max(bonus, 0.30)
                if '攻击+30%' in td: bonus = max(bonus, 0.30)
                if '攻击+25%' in td: bonus = max(bonus, 0.25)
                if '攻击+35%' in td: bonus = max(bonus, 0.35)
                if '攻击力和生命值+20%' in td: bonus = max(bonus, 0.20)
                if '攻命+20%' in td: bonus = max(bonus, 0.20)
                if '攻命+10%' in td: bonus = max(bonus, 0.10)
                if '全属性+25%' in td: bonus = max(bonus, 0.25)
            elif stat == 'hp':
                if '攻击力和生命值+20%' in td: bonus = max(bonus, 0.20)
                if '攻命+20%' in td: bonus = max(bonus, 0.20)
                if '攻命+10%' in td: bonus = max(bonus, 0.10)
                if '全属性+25%' in td: bonus = max(bonus, 0.25)
        return bonus

    @staticmethod
    def calc_aspd(state, op):
        b = 0.0
        for pid, ps in state.pact_states.items():
            if not ps.active:
                continue
            lyr = ps.layers
            has = pid in op.pacts
            if pid == 'agility' and has:
                b += 15 + lyr + (50 if lyr >= 40 else 0)
            elif pid == 'assault' and has and lyr >= 50:
                b += 50
            elif pid == 'sargon' and has:
                b += 50
            elif pid == 'laterano' and has:
                b += 30
            elif pid == 'siracusa' and has:
                b += 50
            elif pid == 'victoria' and has:
                b += (lyr // 3) * 2
        if 'laterano' in op.pacts:
            ls = state.pact_states.get('laterano')
            if ls and ls.active:
                b += (ls.layers // 5) * 2
        base = op.atk_speed
        return base * (100.0 / (100.0 + max(0, b))), b

    @staticmethod
    def apply_trait_effects(op, bo, state):
        """解析所有干员特质描述, 应用战斗特效."""
        e = {'hp_drain': 0, 'regen': 0, 'global_regen': 0,
             'global_regen_pct': 0, 'shield': 0, 'shield_pct': 0,
             'atk_bonus': 0, 'def_bonus': 0, 'hp_bonus': 0,
             'aspd_bonus': 0, 'block_bonus': 0}
        for t in op.traits:
            td = t.description

            # --- 攻防百分比 ---
            if '自身防御+30%' in td: e['def_bonus'] = max(e['def_bonus'], 0.30)
            if '自身攻击力+30%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.30)
            if '每秒损失1%生命' in td: e['hp_drain'] = max(e['hp_drain'], 0.01)
            if '全场每秒回复5生命' in td: e['global_regen'] += 5
            if '全场每秒回复最大生命的2%' in td: e['global_regen_pct'] = max(e['global_regen_pct'], 0.02)
            if '攻击+30%' in td and '回复3生命' in td:
                e['atk_bonus'] = max(e['atk_bonus'], 0.30); e['global_regen'] += 3
            if '防御+50%' in td: e['def_bonus'] = max(e['def_bonus'], 0.50)
            if '防御+40%' in td: e['def_bonus'] = max(e['def_bonus'], 0.40)
            if '阻挡数+1' in td: e['block_bonus'] = max(e['block_bonus'], 1)
            if '全队防御+20%' in td: e['team_def'] = 0.20
            if '攻防+30%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.30); e['def_bonus'] = max(e['def_bonus'], 0.30)
            if '攻击+25%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.25)
            if '攻击+35%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.35)
            if '全属性+25%' in td:
                e['atk_bonus'] = max(e['atk_bonus'], 0.25); e['def_bonus'] = max(e['def_bonus'], 0.25)
                e['hp_bonus'] = max(e['hp_bonus'], 0.25); e['shield'] += 100
            if '生命20%的护盾' in td: e['shield_pct'] = max(e['shield_pct'], 0.20)

            # --- 攻速 ---
            if '攻速+40' in td: e['aspd_bonus'] = max(e['aspd_bonus'], 40)
            if '攻速+60' in td: e['aspd_bonus'] = max(e['aspd_bonus'], 60)
            if '攻速+80' in td: e['aspd_bonus'] = max(e['aspd_bonus'], 80)
            if '攻速+100' in td: e['aspd_bonus'] = max(e['aspd_bonus'], 100)

            # --- 攻命百分比 ---
            if '攻击力和生命值+20%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.20); e['hp_bonus'] = max(e['hp_bonus'], 0.20)
            if '攻命+20%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.20); e['hp_bonus'] = max(e['hp_bonus'], 0.20)
            if '攻命+10%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.10); e['hp_bonus'] = max(e['hp_bonus'], 0.10)
            if '攻击力额外+20%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.20)
            if '攻击力额外+12%' in td: e['atk_bonus'] = max(e['atk_bonus'], 0.12)
            if '防御+10%' in td: e['def_bonus'] = max(e['def_bonus'], 0.10)

        # 应用
        if e['atk_bonus']: bo['atk'] = int(bo['atk'] * (1.0 + e['atk_bonus']))
        if e['def_bonus']: bo['def'] = int(bo['def'] * (1.0 + e['def_bonus']))
        if e['hp_bonus']: bo['hp'] = bo['max_hp'] = int(bo['max_hp'] * (1.0 + e['hp_bonus']))
        if e['aspd_bonus']: bo['atk_spd'] = op.atk_speed * (100.0 / (100.0 + e['aspd_bonus']))
        if e['block_bonus']: bo['block_bonus'] = e['block_bonus']
        if e['shield']: bo['hp'] += e['shield']; bo['max_hp'] += e['shield']
        if e['shield_pct']:
            s = int(bo['max_hp'] * e['shield_pct']); bo['hp'] += s; bo['max_hp'] += s

        bo['_effects'] = e
        return e

    @staticmethod
    def process_tick(bo, rd):
        """每帧处理持续特效(HP流失, 回复等)"""
        eff = bo.get('_effects', {})
        if not eff:
            return
        if eff.get('hp_drain', 0) > 0 and bo['alive']:
            bo['hp'] -= int(bo['max_hp'] * eff['hp_drain'] * rd)
            if bo['hp'] <= 0:
                bo['hp'] = 1
        if eff.get('regen', 0) > 0 and bo['alive']:
            bo['hp'] = min(bo['max_hp'], bo['hp'] + int(eff['regen'] * rd))

    @staticmethod
    def process_global_regen(b_ops, rd):
        """全局回复(调香师, 华法琳, 纯烬艾雅法拉等)"""
        total_regen = 0
        total_regen_pct = 0.0
        for bo in b_ops:
            eff = bo.get('_effects', {})
            if eff.get('global_regen', 0) > 0:
                total_regen += eff['global_regen']
            if eff.get('global_regen_pct', 0) > 0:
                total_regen_pct += eff['global_regen_pct']
        if total_regen > 0 or total_regen_pct > 0:
            for bo in b_ops:
                if bo['alive']:
                    regen = int(total_regen * rd)
                    regen += int(bo['max_hp'] * total_regen_pct * rd)
                    if regen > 0:
                        bo['hp'] = min(bo['max_hp'], bo['hp'] + regen)

    @staticmethod
    def process_healer(bo, b_ops, OX, OY, CS):
        """奶妈逻辑: 治疗范围内最低血量友方。返回(heal_amount, target_x, target_y)或None"""
        if not bo['op'].healer:
            return None
        op_px = OX + bo['gx'] * CS + CS // 2
        op_py = OY + bo['gy'] * CS + CS // 2
        best_ally = None
        lowest_pct = 1.0
        import math
        for ally in b_ops:
            if not ally['alive'] or ally is bo:
                continue
            ax_px = OX + ally['gx'] * CS + CS // 2
            ay_py = OY + ally['gy'] * CS + CS // 2
            if math.hypot(ax_px - op_px, ay_py - op_py) < 200:
                pct = float(ally['hp']) / ally['max_hp']
                if pct < lowest_pct:
                    lowest_pct = pct
                    best_ally = ally
        if best_ally:
            heal = int(bo['atk'] * 0.5)
            best_ally['hp'] = min(best_ally['max_hp'], best_ally['hp'] + heal)
            return (heal, OX + best_ally['gx'] * CS + CS // 2, OY + best_ally['gy'] * CS + CS // 2)
        return None

    @staticmethod
    def process_hp_drain(bo, rd):
        """处理HP持续流失效果"""
        effects = getattr(bo, '_trait_effects', None)
        if effects is None:
            return
        drain = effects.get('hp_drain', 0)
        if drain > 0:
            bo['hp'] -= int(bo['max_hp'] * drain * rd)

    @staticmethod
    def process_regen(b_ops, rd, effects_list):
        """处理全局回复效果"""
        pass
