"""卫戍协议 - 游戏数据定义（基于 PRTS 原文，精简版）"""
from .models import (
    Pact, Operator, Trait, TraitType, TriggerType,
    Enemy, Strategy, WaveConfig
)

# ============================================================
# 一、盟约定义 (8核心 + 12附加 = 20个)
# ============================================================

CORE_PACTS = {
    "yan": Pact(id="yan", name="炎", is_core=True, activate_count=3, advanced_count=6,
        effect_desc="【炎】干员攻击+(23+0.9×层数)%, 生命+一半", group=1),
    "sargon": Pact(id="sargon", name="萨尔贡", is_core=True, activate_count=3, advanced_count=6,
        effect_desc="【萨尔贡】干员攻击+(50+层数)%, 攻速+50, 生命+一半", group=2),
    "victoria": Pact(id="victoria", name="维多利亚", is_core=True, activate_count=3, advanced_count=6,
        effect_desc="【维多利亚】干员攻击+(25+0.8×层数)%, 生命+一半", group=1),
    "kjerag": Pact(id="kjerag", name="谢拉格", is_core=True, activate_count=3, advanced_count=6,
        effect_desc="伤害+25%+每层1%, 生命+一半", group=2),
    "laterano": Pact(id="laterano", name="拉特兰", is_core=True, activate_count=3, advanced_count=6,
        effect_desc="【拉特兰】干员攻速+30, 攻击+(20+0.5×层数)%, 生命+一半", group=3),
    "aegir": Pact(id="aegir", name="阿戈尔", is_core=True, activate_count=3, advanced_count=5,
        effect_desc="生命+(35+层数)%, 攻击+生命加成的3/4", group=3),
    "siracusa": Pact(id="siracusa", name="叙拉古", is_core=True, activate_count=3, advanced_count=6,
        effect_desc="【叙拉古】干员攻速+50, 攻击+(15+0.4×层数)%, 生命+一半", group=4),
    "kazimierz": Pact(id="kazimierz", name="卡西米尔", is_core=True, activate_count=3, advanced_count=6,
        effect_desc="攻击+(50+层数)%, 生命+一半", group=5),
}

EXTRA_PACTS = {
    "precision": Pact(id="precision", name="精准", is_core=False, activate_count=1, advanced_count=3,
        effect_desc="攻击+(10+1.2×层数)%, 生命+一半", group=4),
    "agility": Pact(id="agility", name="灵巧", is_core=False, activate_count=1, advanced_count=40,
        effect_desc="攻速+(15+层数), 再部署-30%; ≥40层额外+50攻速", group=6),
    "arcane": Pact(id="arcane", name="奥术", is_core=False, activate_count=1, advanced_count=3,
        effect_desc="攻击+(20+层数)%", group=6),
    "fortification": Pact(id="fortification", name="坚守", is_core=False, activate_count=1, advanced_count=3,
        effect_desc="生命+(25+1.2×层数)%", group=4),
    "assistance": Pact(id="assistance", name="助力", is_core=False, activate_count=1, advanced_count=3,
        effect_desc="防御+(15+1.2×层数)%, 再部署-30%", group=6),
    "foresight": Pact(id="foresight", name="远见", is_core=False, activate_count=1, advanced_count=80,
        effect_desc="每10层每回合额外+2资金; 刷新时有(18+0.3×层数)%概率免费; 整备区干员也计入激活", group=3),
    "investor": Pact(id="investor", name="投资人", is_core=False, activate_count=1, advanced_count=100,
        effect_desc="'获得时'效果触发2次; ≥100层触发3次; 整备区干员也计入激活", group=1),
    "assault": Pact(id="assault", name="突袭", is_core=False, activate_count=1, advanced_count=50,
        effect_desc="攻击力+(25+层数)%, 生命+(25+层数)%, 再部署-(25+0.2×层数)%; ≥50层攻速+50", group=5),
    "indomitable": Pact(id="indomitable", name="不屈", is_core=False, activate_count=1, advanced_count=3,
        effect_desc="拥有该盟约干员被击倒时(18+0.4×层数)%概率立即半血复活", group=5),
    "harmony": Pact(id="harmony", name="调和", is_core=False, activate_count=1, advanced_count=99,
        effect_desc="核心盟约激活所需在场干员数-1", group=0),
    "solo": Pact(id="solo", name="独行", is_core=False, activate_count=1, advanced_count=99,
        effect_desc="攻命+60%; 场上超过1名独行干员时失效", group=0),
}

ALL_PACTS = {**CORE_PACTS, **EXTRA_PACTS}

def calc_pact_effect(pact_id: str, layers: int) -> float:
    """计算盟约效果值(供旧引擎使用)"""
    p = ALL_PACTS.get(pact_id)
    return float(layers) if p else 0.0

# ============================================================
# 二、干员定义
# ============================================================

OPERATORS = [
    # === Ⅰ阶 ===
    Operator(id="texas", name="德克萨斯", tier=1, cost=1, pacts=["siracusa", "solo"],
        traits=[Trait(TraitType.PREP, TriggerType.ON_OBTAIN, None, 0, 0, "<获得时>获得1次免费刷新")],
        base_hp=1100, base_atk=300, base_def=120, block_count=2),
    Operator(id="leizi", name="惊蛰", tier=1, cost=1, pacts=["yan"],
        traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_OBTAIN, "yan", 1, 2, "<获得时>获得等于调度中心等级的【炎】层数(精锐翻倍)")],
        base_hp=800, base_atk=280, base_def=80, atk_speed=1.6, deploy_cost=10),
    Operator(id="estelle", name="艾丝黛尔", tier=1, cost=1, pacts=["sargon"],
        traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_OBTAIN, "sargon", 2, 4, "<获得时>【萨尔贡】层数+2(精锐+4)")],
        base_hp=1200, base_atk=250, base_def=100, block_count=2),
    Operator(id="cirmai", name="刺玫", tier=1, cost=1, pacts=["victoria", "assistance"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "victoria", 1, 2, "<休整期结束时>【维多利亚】层数+1(精锐+2)")],
        base_hp=700, base_atk=320, base_def=60, healer=True),
    Operator(id="jiaofeng", name="角峰", tier=1, cost=1, pacts=["kjerag", "fortification"],
        traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_OBTAIN, None, 1, 2, "<获得时>自身盟约层数+1(精锐+2)")],
        base_hp=1500, base_atk=200, base_def=150, block_count=3),
    Operator(id="yinxian", name="隐现", tier=1, cost=1, pacts=["laterano", "agility"],
        traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "laterano", 2, 2, "<战斗开始时>【拉特兰】层数+2(精锐+2), 每叠5层攻速+2")],
        base_hp=750, base_atk=350, base_def=70, atk_speed=1.0),
    Operator(id="deepcruise", name="深巡", tier=1, cost=1, pacts=["aegir"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "aegir", 1, 2, "<战斗开始时>【阿戈尔】层数+1(精锐+2), 攻击力额外+20%")],
        base_hp=900, base_atk=300, base_def=90),
    Operator(id="provence", name="普罗旺斯", tier=1, cost=1, pacts=["siracusa"],
        traits=[Trait(TraitType.PREP, TriggerType.ON_OBTAIN, None, 0, 0, "<获得时>获得1次免费刷新(精锐2次)")],
        base_hp=800, base_atk=380, base_def=70),
    Operator(id="wildmane", name="野鬃", tier=1, cost=1, pacts=["kazimierz", "agility"],
        traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_OBTAIN, None, 2, 4, "<获得时>自身盟约层数+2(精锐+4)")],
        base_hp=850, base_atk=290, base_def=80, block_count=1),
    Operator(id="pact_support", name="盟约·辅助干员", tier=1, cost=1, pacts=["harmony"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "harmony", 1, 2, "<战斗开始时>【调和】层数+1(精锐+2), 攻命+20%")],
        base_hp=1000, base_atk=300, base_def=100),

    # === Ⅱ阶 ===
    Operator(id="xiaoman", name="小满", tier=2, cost=2, pacts=["yan", "agility"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "yan", 1, 2, "<休整期结束时>【炎】层数+1(精锐+2)")],
        base_hp=900, base_atk=340, base_def=90),
    Operator(id="shacao", name="莎草", tier=2, cost=2, pacts=["sargon"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "sargon", 5, 10, "<战斗开始时>【萨尔贡】层数+5(精锐+10)")],
        base_hp=850, base_atk=360, base_def=80, healer=True),
    Operator(id="harold", name="哈洛德", tier=2, cost=2, pacts=["kjerag", "victoria"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kjerag", 2, 4, "<战斗开始时>【谢拉格】层数+2(精锐+4), 攻命+20%")],
        base_hp=1100, base_atk=310, base_def=110),
    Operator(id="excu", name="送葬人", tier=2, cost=2, pacts=["laterano", "precision"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "precision", 3, 6, "<战斗开始时>【精准】层数+3(精锐+6)")],
        base_hp=950, base_atk=400, base_def=85, atk_speed=1.2),
    Operator(id="ghost_shark", name="幽灵鲨", tier=2, cost=2, pacts=["aegir"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_DEFEAT, "aegir", 1, 2, "<被击倒时>【阿戈尔】层数+1(精锐+2)")],
        base_hp=1300, base_atk=350, base_def=120, block_count=2),
    Operator(id="lappland", name="拉普兰德", tier=2, cost=2, pacts=["siracusa"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REFRESH, "siracusa", 4, 8, "<刷新时>【叙拉古】层数+4(精锐+8)")],
        base_hp=1000, base_atk=420, base_def=100, block_count=2),
    Operator(id="gravel", name="砾", tier=2, cost=2, pacts=["kazimierz", "indomitable"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kazimierz", 2, 2, "<战斗开始时>【卡西米尔】+2"),
                Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_DEFEAT, "indomitable", 4, 4, "<被击倒时>【不屈】+4")],
        base_hp=800, base_atk=280, base_def=130, redeploy_time=30, block_count=1),
    Operator(id="bubble", name="泡泡", tier=2, cost=2, pacts=["sargon", "fortification"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "fortification", 2, 4, "<战斗开始时>【坚守】层数+2(精锐+4), 防御+10%")],
        base_hp=1600, base_atk=180, base_def=200, block_count=3),
    Operator(id="humus", name="休谟斯", tier=2, cost=2, pacts=["assault"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "assault", 1, 2, "<战斗开始时>【突袭】层数+1(精锐+2)")],
        base_hp=1100, base_atk=380, base_def=100, block_count=2),

    # === Ⅲ阶 ===
    Operator(id="swire", name="诗怀雅", tier=3, cost=3, pacts=["yan"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REFRESH, "yan", 4, 8, "<刷新时>【炎】层数+4(精锐+8)")],
        base_hp=1200, base_atk=420, base_def=140),
    Operator(id="philae", name="菲莱", tier=3, cost=3, pacts=["kazimierz", "precision"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kazimierz", 6, 12, "<战斗开始时>【卡西米尔】【精准】层数+6(精锐+12)")],
        base_hp=1100, base_atk=380, base_def=130, block_count=2),
    Operator(id="angel", name="能天使", tier=3, cost=3, pacts=["laterano", "foresight"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "laterano", 1, 2, "<战斗开始时>【拉特兰】【远见】层数+1(精锐+2)")],
        base_hp=900, base_atk=480, base_def=90, atk_speed=0.85),
    Operator(id="thin_green", name="薄绿", tier=3, cost=3, pacts=["kjerag"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kjerag", 1, 2, "<战斗开始时>【谢拉格】层数+1(精锐+2)")],
        base_hp=850, base_atk=450, base_def=75),
    Operator(id="first_snow", name="初雪", tier=3, cost=3, pacts=["kjerag", "investor", "agility"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REFRESH, "kjerag", 4, 8, "<刷新时>【谢拉格】层数+4(精锐+8)")],
        base_hp=950, base_atk=400, base_def=100),

    # === Ⅳ阶 ===
    Operator(id="silverash", name="银灰", tier=4, cost=5, pacts=["kjerag", "investor", "agility"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kjerag", 3, 6, "<战斗开始时>【谢拉格】层数+3(精锐+6)")],
        base_hp=1400, base_atk=550, base_def=160, block_count=2),
    Operator(id="skadi", name="斯卡蒂", tier=4, cost=5, pacts=["aegir", "indomitable"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_DEFEAT, "aegir", 1, 2, "<被击倒时>【阿戈尔】【不屈】层数各+1(精锐+2)")],
        base_hp=1600, base_atk=600, base_def=140, block_count=1),
    Operator(id="swire_l", name="琳琅诗怀雅", tier=4, cost=5, pacts=["victoria"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "victoria", 1, 2, "<休整期结束时>场上每名不同阶【维多利亚】干员层数+1(精锐+2)")],
        base_hp=1300, base_atk=480, base_def=150),
    Operator(id="bagpipe", name="风笛", tier=4, cost=5, pacts=["victoria", "assault"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REFRESH, "victoria", 4, 8, "<刷新时>【维多利亚】层数+4(精锐+8)")],
        base_hp=1200, base_atk=520, base_def=130, deploy_cost=8, block_count=1),

    # === Ⅴ阶 ===
    Operator(id="mlynar", name="玛恩纳", tier=5, cost=8, pacts=["kazimierz"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kazimierz", 5, 10, "<战斗开始时>【卡西米尔】层数+5(精锐+10), 攻击力额外+20%")],
        base_hp=1800, base_atk=550, base_def=200, block_count=2),
    Operator(id="reed_flame", name="焰影苇草", tier=5, cost=8, pacts=["victoria", "precision"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "victoria", 2, 4, "<战斗开始时>【维多利亚】层数+2(精锐+4), 每叠3层攻速+2")],
        base_hp=1100, base_atk=620, base_def=100),
    Operator(id="texas_alt", name="缄默德克萨斯", tier=5, cost=8, pacts=["siracusa"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, None, 1, 2, "<休整期结束时>自身已激活盟约层数+1(精锐+2)")],
        base_hp=1300, base_atk=580, base_def=140, redeploy_time=30),
    Operator(id="ulpianus", name="乌尔比安", tier=5, cost=8, pacts=["aegir"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "aegir", 3, 6, "<战斗开始时>【阿戈尔】层数+3(精锐+6)")],
        base_hp=2000, base_atk=650, base_def=180, block_count=2),
    Operator(id="surtr", name="史尔特尔", tier=5, cost=8, pacts=["assault", "arcane"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "assault", 1, 2, "<战斗开始时>【突袭】层数+1(精锐+2)")],
        base_hp=1400, base_atk=700, base_def=120, block_count=1),
    Operator(id="gnosis", name="灵知", tier=5, cost=8, pacts=["kjerag", "arcane"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_START, None, 1, 2, "<进入休整期时>自身及身前干员已激活盟约各+1(精锐+2)")],
        base_hp=1100, base_atk=500, base_def=100),
    Operator(id="gladiia", name="歌蕾蒂娅", tier=5, cost=8, pacts=["aegir", "assault"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "aegir", 2, 4, "<休整期结束时>【阿戈尔】【突袭】层数各+2(精锐+4)")],
        base_hp=1500, base_atk=550, base_def=150, block_count=2),

    # === Ⅵ阶 ===
    Operator(id="yue", name="余", tier=6, cost=12, pacts=["yan", "fortification"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_START, "yan", 4, 8, "<进入休整期时>【炎】层数+4(精锐+8)")],
        base_hp=2000, base_atk=600, base_def=220, block_count=3),
    Operator(id="skadi_corrupt", name="浊心斯卡蒂", tier=6, cost=12, pacts=["aegir"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "aegir", 5, 10, "<战斗开始时>【阿戈尔】层数+5(精锐+10)")],
        base_hp=1800, base_atk=500, base_def=160),
    Operator(id="passenger", name="异客", tier=6, cost=12, pacts=["sargon", "agility", "precision"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "sargon", 4, 8, "<战斗开始时>【萨尔贡】层数+4(精锐+8), 攻击力额外+12%")],
        base_hp=1200, base_atk=680, base_def=100, atk_speed=1.6),
    Operator(id="reed_victoria", name="维娜·维多利亚", tier=6, cost=12, pacts=["victoria", "foresight"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "victoria", 3, 6, "<休整期结束时>场上每名不同阶【维多利亚】干员使【维多利亚】+3(精锐+6)")],
        base_hp=2200, base_atk=650, base_def=200, block_count=2),
    Operator(id="muelsyse", name="缪尔赛思", tier=6, cost=12, pacts=["harmony"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_OBTAIN, "harmony", 3, 6, "<获得时>【调和】层数+3(精锐+6)")],
        base_hp=1400, base_atk=550, base_def=140),
    Operator(id="nearl_radiant", name="耀骑士临光", tier=6, cost=12, pacts=["kazimierz", "assault"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kazimierz", 5, 10, "<战斗开始时>【卡西米尔】层数+5(精锐+10)")],
        base_hp=2000, base_atk=700, base_def=180, block_count=1),
    Operator(id="saint_angel", name="圣约送葬人", tier=6, cost=12, pacts=["laterano", "precision"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "laterano", 1, 2, "<战斗开始时>【拉特兰】层数+1(精锐+2)")],
        base_hp=1500, base_atk=620, base_def=150, atk_speed=0.9),
    # === 新增71名干员(PRTS数据) ===
    # I阶
    Operator(id="yueyue", name="跃跃", tier=1, cost=1, pacts=["precision"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "precision", 1, 2, "<战斗开始时>【精准】层数+1(精锐+2)")], base_hp=800, base_atk=340, base_def=70, atk_speed=1.0),
    Operator(id="gumi", name="古米", tier=1, cost=1, pacts=["fortification"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "fortification", 1, 2, "<战斗开始时>自身防御+30%, 【坚守】层数+1(精锐+2)")], base_hp=1400, base_atk=220, base_def=140, atk_speed=1.5, block_count=3),
    Operator(id="podengo", name="波登可", tier=1, cost=1, pacts=["assistance"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "assistance", 1, 2, "<休整期结束时>【助力】层数+1(精锐+2)")], base_hp=700, base_atk=300, base_def=60, atk_speed=1.6),
    Operator(id="greyy", name="格雷伊", tier=1, cost=1, pacts=["agility"], traits=[Trait(TraitType.PREP, TriggerType.ON_OBTAIN, "", 0, 0, "<获得时>额外获得2资金")], base_hp=750, base_atk=320, base_def=65, atk_speed=1.6),
    Operator(id="indigo", name="深靛", tier=1, cost=1, pacts=["arcane","precision"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_OBTAIN, "arcane", 2, 4, "<获得时>【奥术】层数+2(精锐+4)")], base_hp=800, base_atk=350, base_def=55, atk_speed=1.6),
    Operator(id="utage", name="宴", tier=1, cost=1, pacts=["assault"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 1, 2, "<战斗开始时>自身攻击力+30%, 每秒损失1%生命")], base_hp=1100, base_atk=380, base_def=80, atk_speed=1.5, block_count=1),
    Operator(id="liskarm", name="雷蛇", tier=1, cost=1, pacts=["indomitable"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_DEFEAT, "indomitable", 2, 4, "<被击倒时>【不屈】层数+2(精锐+4)")], base_hp=1300, base_atk=250, base_def=170, atk_speed=1.2, block_count=3),
    # II阶
    Operator(id="silence", name="赫默", tier=2, cost=2, pacts=["foresight"], traits=[Trait(TraitType.PREP, TriggerType.ON_REST_END, "foresight", 2, 4, "<休整期结束时>【远见】层数+2(精锐+4)")], base_hp=850, base_atk=370, base_def=80, atk_speed=1.6, healer=True),
    Operator(id="luoluo", name="洛洛", tier=2, cost=2, pacts=["victoria","arcane"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "victoria", 2, 4, "<休整期结束时>【维多利亚】层数+2(精锐+4)")], base_hp=900, base_atk=400, base_def=75, atk_speed=1.6),
    Operator(id="kazemaru", name="风丸", tier=2, cost=2, pacts=["solo", "foresight"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_COMBAT_START, "solo", 2, 4, "<战斗开始时>【独行】层数+2(精锐+4)")], base_hp=950, base_atk=430, base_def=70, atk_speed=1.0),
    Operator(id="tibi", name="蒂比", tier=2, cost=2, pacts=["agility"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "agility", 2, 4, "<休整期结束时>【灵巧】层数+2(精锐+4)")], base_hp=880, base_atk=380, base_def=85, atk_speed=1.3, block_count=1),
    Operator(id="perfumer", name="调香师", tier=2, cost=2, pacts=["assistance"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 1, 2, "<战斗开始时>全场每秒回复5生命")], base_hp=750, base_atk=350, base_def=70, atk_speed=1.6, healer=True),
    Operator(id="zheya", name="折桠", tier=2, cost=2, pacts=["fortification","solo"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_DEFEAT, "fortification", 3, 6, "<被击倒时>【坚守】层数+3(精锐+6)")], base_hp=1300, base_atk=300, base_def=150, atk_speed=1.5, block_count=2),
    Operator(id="huihao", name="灰毫", tier=2, cost=2, pacts=["kazimierz","fortification"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_COMBAT_START, "kazimierz", 3, 6, "<战斗开始时>【卡西米尔】层数+3(精锐+6)")], base_hp=1400, base_atk=280, base_def=160, atk_speed=1.5, block_count=3),
    Operator(id="xiren", name="锡人", tier=2, cost=2, pacts=["investor","agility"], traits=[Trait(TraitType.PREP, TriggerType.ON_OBTAIN, "", 0, 0, "<获得时>下次商店刷新免费")], base_hp=900, base_atk=360, base_def=75, atk_speed=1.6),
    # III阶
    Operator(id="duanya", name="断崖", tier=3, cost=3, pacts=["agility"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "agility", 3, 6, "<战斗开始时>【灵巧】层数+3(精锐+6)")], base_hp=1200, base_atk=480, base_def=130, atk_speed=1.2, block_count=2),
    Operator(id="haini", name="海霓", tier=3, cost=3, pacts=["aegir","arcane"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REFRESH, "aegir", 4, 8, "<刷新时>【阿戈尔】层数+4(精锐+8)")],
        base_hp=1000, base_atk=500, base_def=90, atk_speed=1.5),
    Operator(id="songguo", name="松果", tier=3, cost=3, pacts=["agility"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 2, 4, "<战斗开始时>攻速+40, 持续整场")], base_hp=1150, base_atk=460, base_def=120, atk_speed=1.2, block_count=2),
    Operator(id="xuelie", name="雪猎", tier=3, cost=3, pacts=["kjerag","precision"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_COMBAT_START, "kjerag", 4, 8, "<战斗开始时>【谢拉格】层数+4(精锐+8, 单次)")], base_hp=1100, base_atk=470, base_def=110, atk_speed=1.0, block_count=1),
    Operator(id="xiaguang", name="瑕光", tier=3, cost=3, pacts=["kazimierz","assault"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "kazimierz", 4, 8, "<休整期结束时>【卡西米尔】层数+4(精锐+8)")], base_hp=1300, base_atk=440, base_def=160, atk_speed=1.5, block_count=2),
    Operator(id="zhijian", name="至简", tier=3, cost=3, pacts=["sargon","agility"], traits=[Trait(TraitType.PREP, TriggerType.ON_OBTAIN, "", 0, 0, "<获得时>调度中心临时等级+1(本回合)")], base_hp=1050, base_atk=490, base_def=100, atk_speed=1.6),
    Operator(id="shetuxiang", name="蛇屠箱", tier=3, cost=3, pacts=["fortification","indomitable"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 3, 6, "<战斗开始时>防御+50%, 阻挡数+1")], base_hp=1600, base_atk=300, base_def=200, atk_speed=1.5, block_count=3),
    Operator(id="liuxing", name="流星", tier=3, cost=3, pacts=["kazimierz","solo"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REFRESH, "kazimierz", 4, 8, "<刷新时>【卡西米尔】层数+4(精锐+8)")],
        base_hp=1100, base_atk=500, base_def=95, atk_speed=1.0),
    Operator(id="rendong", name="忍冬", tier=3, cost=3, pacts=["siracusa","agility"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_START, "siracusa", 3, 6, "<进入休整期时>【叙拉古】层数+3(精锐+6)")], base_hp=1200, base_atk=480, base_def=130, atk_speed=1.2, block_count=2),
    Operator(id="siye", name="伺夜", tier=3, cost=3, pacts=["siracusa", "foresight"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "siracusa", 4, 8, "<战斗开始时>【叙拉古】层数+4(精锐+8)")], base_hp=1000, base_atk=460, base_def=85, atk_speed=1.0),
    Operator(id="yela", name="耶拉", tier=3, cost=3, pacts=["kjerag","assistance"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "kjerag", 3, 6, "<休整期结束时>【谢拉格】层数+3(精锐+6)")], base_hp=1100, base_atk=450, base_def=100, atk_speed=1.6),
    Operator(id="kongxian", name="空弦", tier=3, cost=3, pacts=["laterano","agility"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REFRESH, "laterano", 4, 8, "<刷新时>【拉特兰】层数+4(精锐+8)")],
        base_hp=950, base_atk=520, base_def=80, atk_speed=0.9),
    # IV阶
    Operator(id="xinyangjiaobanji", name="信仰搅拌机", tier=4, cost=5, pacts=["laterano","fortification"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "laterano", 4, 8, "<战斗开始时>【拉特兰】层数+4(精锐+8)")], base_hp=1500, base_atk=500, base_def=180, atk_speed=1.5, block_count=3),
    Operator(id="mostima", name="莫斯提马", tier=4, cost=5, pacts=["laterano","arcane"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "arcane", 4, 8, "<休整期结束时>【奥术】层数+4(精锐+8)")], base_hp=1200, base_atk=580, base_def=100, atk_speed=1.6),
    Operator(id="yineisi", name="伊内丝", tier=4, cost=5, pacts=["foresight","assault"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_COMBAT_START, "foresight", 6, 12, "<战斗开始时>【远见】层数+6(精锐+12, 单次)")], base_hp=1400, base_atk=520, base_def=140, atk_speed=1.0, block_count=2),
    Operator(id="hanmangkeluosi", name="寒芒克洛丝", tier=4, cost=5, pacts=["precision"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 3, 6, "<战斗开始时>攻速+60")], base_hp=1100, base_atk=560, base_def=90, atk_speed=0.9),
    Operator(id="shuiyue", name="水月", tier=4, cost=5, pacts=["aegir","solo"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_DEFEAT, "aegir", 5, 10, "<被击倒时>【阿戈尔】层数+5(精锐+10)")], base_hp=1300, base_atk=550, base_def=120, atk_speed=1.2, block_count=1),
    Operator(id="aluoma", name="阿罗玛", tier=4, cost=5, pacts=["siracusa","arcane"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_START, "siracusa", 4, 8, "<进入休整期时>【叙拉古】层数+4(精锐+8)")], base_hp=1200, base_atk=540, base_def=110, atk_speed=1.5),
    Operator(id="kaiselin", name="凯瑟琳", tier=4, cost=5, pacts=["victoria","agility"], traits=[Trait(TraitType.PREP, TriggerType.ON_OBTAIN, "", 0, 0, "<获得时>升级中心费用-2(本局永久)")], base_hp=1400, base_atk=500, base_def=150, atk_speed=1.5, block_count=2),
    Operator(id="laienhate", name="莱恩哈特", tier=4, cost=5, pacts=["agility","precision"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "agility", 4, 8, "<战斗开始时>【灵巧】层数+4(精锐+8)")], base_hp=1150, base_atk=530, base_def=100, atk_speed=1.3),
    Operator(id="xingxiong", name="星熊", tier=4, cost=5, pacts=["yan"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 4, 8, "<战斗开始时>防御+40%, 阻挡数+1")], base_hp=1800, base_atk=400, base_def=220, atk_speed=1.5, block_count=3),
    Operator(id="niyan", name="泥岩", tier=4, cost=5, pacts=["solo"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 5, 10, "<战斗开始时>获得相当于生命20%的护盾")], base_hp=2000, base_atk=480, base_def=200, atk_speed=1.5, block_count=3),
    Operator(id="yanwei", name="焰尾", tier=4, cost=5, pacts=["kazimierz"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kazimierz", 4, 8, "<战斗开始时>【卡西米尔】层数+4(精锐+8)")], base_hp=1300, base_atk=520, base_def=150, atk_speed=1.0, block_count=1),
    Operator(id="yuanya", name="远牙", tier=4, cost=5, pacts=["kazimierz","precision"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "kazimierz", 5, 10, "<战斗开始时>【卡西米尔】层数+5(精锐+10)")], base_hp=1000, base_atk=600, base_def=80, atk_speed=1.0),
    Operator(id="baimianxiao", name="白面鸮", tier=4, cost=5, pacts=["assistance","agility"], traits=[Trait(TraitType.PREP, TriggerType.ON_OBTAIN, "", 0, 0, "<获得时>获得2次免费刷新")], base_hp=950, base_atk=480, base_def=85, atk_speed=1.6, healer=True),
    Operator(id="bailianjiaweier", name="百炼嘉维尔", tier=4, cost=5, pacts=["sargon"],
        traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REFRESH, "sargon", 4, 8, "<刷新时>【萨尔贡】层数+4(精锐+8)")],
        base_hp=1500, base_atk=550, base_def=150, atk_speed=1.2, block_count=2),
    Operator(id="kanielian", name="卡涅利安", tier=4, cost=5, pacts=["sargon","assistance"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "sargon", 4, 8, "<休整期结束时>【萨尔贡】层数+4(精锐+8)")], base_hp=1300, base_atk=520, base_def=140, atk_speed=1.6),
    Operator(id="mowang", name="魔王", tier=4, cost=5, pacts=["harmony"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "harmony", 4, 8, "<休整期结束时>【调和】层数+4(精锐+8)")], base_hp=1400, base_atk=500, base_def=130, atk_speed=1.5),
    Operator(id="huafalin", name="华法琳", tier=4, cost=5, pacts=["solo", "foresight"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 4, 8, "<战斗开始时>攻击+30%, 全场每秒回复3生命")], base_hp=1100, base_atk=520, base_def=90, atk_speed=1.6, healer=True),
    # V阶
    Operator(id="nifu", name="妮芙", tier=5, cost=8, pacts=["agility"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "agility", 5, 10, "<休整期结束时>【灵巧】层数+5(精锐+10)")], base_hp=1200, base_atk=620, base_def=95, atk_speed=1.0),
    Operator(id="titi", name="缇缇", tier=5, cost=8, pacts=["sargon","precision"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_COMBAT_START, "sargon", 8, 16, "<战斗开始时>【萨尔贡】层数+8(精锐+16, 单次)")], base_hp=1400, base_atk=600, base_def=140, atk_speed=1.2, block_count=1),
    Operator(id="zhuhuang", name="烛煌", tier=5, cost=8, pacts=["victoria","yan"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 5, 10, "<战斗开始时>攻击+25%")], base_hp=1500, base_atk=650, base_def=170, atk_speed=1.5, block_count=2),
    Operator(id="yindelaixi", name="隐德来希", tier=5, cost=8, pacts=["indomitable","agility"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_DEFEAT, "indomitable", 6, 12, "<被击倒时>【不屈】层数+6(精锐+12)")], base_hp=1600, base_atk=580, base_def=150, atk_speed=1.2, block_count=2),
    Operator(id="haojiao", name="号角", tier=5, cost=8, pacts=["victoria"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 5, 10, "<战斗开始时>攻防+30%, 阻挡数+1")], base_hp=2100, base_atk=550, base_def=210, atk_speed=1.5, block_count=3),
    Operator(id="linglan", name="铃兰", tier=5, cost=8, pacts=["siracusa","harmony"], traits=[Trait(TraitType.PREP, TriggerType.ON_REST_END, "", 0, 0, "<休整期结束时>随机1名已激活盟约层数+5")], base_hp=1100, base_atk=500, base_def=100, atk_speed=1.6, healer=True),
    Operator(id="saireiya", name="塞雷娅", tier=5, cost=8, pacts=["fortification","solo"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 5, 10, "<战斗开始时>全队防御+20%, 自己防御额外+40%")], base_hp=2200, base_atk=450, base_def=250, atk_speed=1.5, block_count=3),
    Operator(id="xi", name="夕", tier=5, cost=8, pacts=["yan","arcane"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "yan", 5, 10, "<战斗开始时>【炎】层数+5(精锐+10)")], base_hp=1300, base_atk=650, base_def=110, atk_speed=1.6),
    Operator(id="guimingyouling", name="归溟幽灵鲨", tier=5, cost=8, pacts=["aegir","indomitable"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_DEFEAT, "aegir", 6, 12, "<被击倒时>【阿戈尔】层数+6(精锐+12)")], base_hp=1800, base_atk=600, base_def=160, atk_speed=1.2, block_count=2),
    Operator(id="linyuyinhui", name="凛御银灰", tier=5, cost=8, pacts=["kjerag","investor","agility"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_COMBAT_START, "kjerag", 8, 16, "<战斗开始时>【谢拉格】层数+8(精锐+16, 单次)")], base_hp=1600, base_atk=620, base_def=170, atk_speed=1.2, block_count=2),
    Operator(id="yinxingjici", name="引星棘刺", tier=5, cost=8, pacts=["agility", "foresight"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 5, 10, "<战斗开始时>攻速+80")], base_hp=1400, base_atk=640, base_def=130, atk_speed=1.0, block_count=2),
    Operator(id="shan", name="山", tier=5, cost=8, pacts=["investor"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "investor", 5, 10, "<休整期结束时>【投资人】层数+5(精锐+10)")], base_hp=1800, base_atk=580, base_def=180, atk_speed=1.0, block_count=2),
    Operator(id="anjielinna", name="安洁莉娜", tier=5, cost=8, pacts=["siracusa", "foresight"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_START, "siracusa", 5, 10, "<进入休整期时>【叙拉古】层数+5(精锐+10)")], base_hp=1000, base_atk=560, base_def=85, atk_speed=1.6),
    Operator(id="hantan", name="寒檀", tier=5, cost=8, pacts=["foresight"], traits=[Trait(TraitType.PREP, TriggerType.ON_REST_END, "", 0, 0, "<休整期结束时>额外+3资金")], base_hp=1200, base_atk=600, base_def=100, atk_speed=1.6),
    Operator(id="luwuguan", name="录武官", tier=5, cost=8, pacts=["yan", "foresight"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_OBTAIN, "yan", 6, 12, "<获得时>【炎】层数+6(精锐+12)(单次)")], base_hp=1500, base_atk=580, base_def=160, atk_speed=1.5, block_count=2, healer=True),
    # VI阶
    Operator(id="leimuan", name="蕾缪安", tier=6, cost=12, pacts=["laterano","precision"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "laterano", 6, 12, "<战斗开始时>【拉特兰】层数+6(精锐+12)")], base_hp=1600, base_atk=680, base_def=150, atk_speed=0.9),
    Operator(id="shenglingchuxue", name="圣聆初雪", tier=6, cost=12, pacts=["kjerag","arcane"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "kjerag", 6, 12, "<休整期结束时>【谢拉格】层数+6(精锐+12)")], base_hp=1500, base_atk=650, base_def=140, atk_speed=1.5),
    Operator(id="peipei", name="佩佩", tier=6, cost=12, pacts=["sargon","indomitable"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 6, 12, "<战斗开始时>全属性+25%, 获得额外100生命护盾")], base_hp=2000, base_atk=680, base_def=200, atk_speed=1.2, block_count=2),
    Operator(id="suxin", name="塑心", tier=6, cost=12, pacts=["laterano"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_END, "laterano", 6, 12, "<休整期结束时>【拉特兰】层数+6(精锐+12)")], base_hp=1400, base_atk=700, base_def=130, atk_speed=1.5),
    Operator(id="midiexiang", name="迷迭香", tier=6, cost=12, pacts=["precision","foresight","harmony"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_COMBAT_START, "precision", 10, 20, "<战斗开始时>【精准】层数+10(精锐+20, 单次)")], base_hp=1500, base_atk=720, base_def=140, atk_speed=1.0),
    Operator(id="xinyuenengtianshi", name="新约能天使", tier=6, cost=12, pacts=["laterano"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 6, 12, "<战斗开始时>攻速+100")], base_hp=1300, base_atk=750, base_def=100, atk_speed=0.85),
    Operator(id="liuming", name="流明", tier=6, cost=12, pacts=["assistance"], traits=[Trait(TraitType.PREP, TriggerType.ON_REST_END, "", 0, 0, "<休整期结束时>回复2点目标生命")], base_hp=1400, base_atk=550, base_def=120, atk_speed=1.6),
    Operator(id="qiubai", name="仇白", tier=6, cost=12, pacts=["yan","assault"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_COMBAT_START, "yan", 6, 12, "<战斗开始时>【炎】层数+6(精锐+12)")], base_hp=1900, base_atk=700, base_def=190, atk_speed=1.2, block_count=2),
    Operator(id="suguangxingyuan", name="溯光星源", tier=6, cost=12, pacts=["arcane","agility"], traits=[Trait(TraitType.STACK_CONTINUOUS, TriggerType.ON_REST_START, "arcane", 6, 12, "<进入休整期时>【奥术】层数+6(精锐+12)")], base_hp=1400, base_atk=680, base_def=120, atk_speed=1.6),
    Operator(id="huangwulapulande", name="荒芜拉普兰德", tier=6, cost=12, pacts=["siracusa"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 6, 12, "<战斗开始时>攻击+35%")], base_hp=1700, base_atk=720, base_def=160, atk_speed=1.2, block_count=2),
    Operator(id="jian", name="锏", tier=6, cost=12, pacts=["kjerag","kazimierz","agility"], traits=[Trait(TraitType.STACK_SINGLE, TriggerType.ON_COMBAT_START, "kjerag", 10, 20, "<战斗开始时>【谢拉格】层数+10(精锐+20, 单次)")], base_hp=1800, base_atk=700, base_def=180, atk_speed=1.0, block_count=2),
    Operator(id="chunjinaiyafala", name="纯烬艾雅法拉", tier=6, cost=12, pacts=["assistance"], traits=[Trait(TraitType.COMBAT, TriggerType.ON_COMBAT_START, "", 6, 12, "<战斗开始时>全场每秒回复最大生命的2%")], base_hp=1200, base_atk=650, base_def=100, atk_speed=1.6, healer=True),
]

OPS_BY_TIER = {i: [op for op in OPERATORS if op.tier == i] for i in range(1, 7)}

# ============================================================
# 三、策略定义 (精简为11个, 删除装备相关)
# ============================================================

STRATEGIES = [
    Strategy("s1", "重点监护", "华法琳", 28, "每回合已激活盟约层数+8"),
    Strategy("s2", "众志合一", "阿米娅", 25, "3/4/5+已激活盟约: +20/30/40%攻击力/生命值"),
    Strategy("s3", "坚不可摧", "歌利亚", 45, "初始生命值45"),
    Strategy("s4", "理财达人", "坎诺特", 27, "每回合获得持有资金的10%向上取整"),
    Strategy("s5", "以己之长", "陈", 22, "所有干员攻击无视敌人25%防御力"),
    Strategy("s6", "优等生", "Pith", 24, "开局获得一个随机VI阶干员"),
    Strategy("s7", "御守之力", "铃兰", 20, "每回合触发1名干员'获得时'效果"),
    Strategy("s8", "文火慢炖", "余", 27, "T8: 仅1个已激活盟约+36层, 否则每个已激活盟约+12层"),
    Strategy("s9", "定向投放", "凯瑟琳", 26, "升级调度中心费用减半"),
    Strategy("s10", "业务指标", "玛恩纳", 24, "每购买【卡西米尔】干员+1资金(最多3/回合)"),
    Strategy("s11", "雪域礼赠", "休露丝", 24, "每回合首位购买【谢拉格】干员返还1资金"),
]

# ============================================================
# 四、敌人定义
# ============================================================

ENEMIES = {
    "grunt": Enemy(id="grunt", name="源石虫", hp=800, max_hp=800, atk=80, defense=20, speed=1.5),
    "hound": Enemy(id="hound", name="猎狗", hp=600, max_hp=600, atk=120, defense=0, speed=2.0),
    "soldier": Enemy(id="soldier", name="整合运动士兵", hp=1500, max_hp=1500, atk=150, defense=80, speed=1.0),
    "caster": Enemy(id="caster", name="整合运动术师", hp=1000, max_hp=1000, atk=250, defense=40, speed=0.8),
    "heavy": Enemy(id="heavy", name="重装敌人", hp=3000, max_hp=3000, atk=200, defense=200, speed=0.5),
    "sniper": Enemy(id="sniper", name="整合运动狙击手", hp=900, max_hp=900, atk=300, defense=30, speed=0.7),
    "elite": Enemy(id="elite", name="精英战士", hp=5000, max_hp=5000, atk=350, defense=150, speed=0.8, is_elite=True),
    "elite_caster": Enemy(id="elite_caster", name="精英术师", hp=3500, max_hp=3500, atk=500, defense=80, speed=0.6, is_elite=True),
    "drone": Enemy(id="drone", name="无人机", hp=600, max_hp=600, atk=100, defense=10, speed=2.0),
    "big_drone": Enemy(id="big_drone", name="重型无人机", hp=2000, max_hp=2000, atk=200, defense=30, speed=1.5),
    "boss": Enemy(id="boss", name="领袖·整合之影", hp=30000, max_hp=30000, atk=500, defense=300, speed=0.6, is_elite=True, is_boss=True),
}

# ============================================================
# 五、波次配置
# ============================================================

def generate_waves(difficulty: str = "standard") -> list:
    mult = {"入门": 0.5, "标准": 1.0, "险境": 1.5, "绝境": 2.0, "终极": 3.0}.get(difficulty, 1.0)
    waves = []
    for i in range(1, 16):
        if i <= 3: enemies = [("grunt", 2+i), ("hound", i)]
        elif i <= 6: enemies = [("grunt", 3), ("soldier", i-1), ("hound", 2)]
        elif i <= 9: enemies = [("soldier", 3), ("caster", i-5), ("drone", 1), ("sniper", 1)]
        elif i <= 12: enemies = [("soldier", 4), ("heavy", i-8), ("caster", 2), ("drone", 2)]
        elif i <= 14: enemies = [("heavy", 3), ("elite", 1), ("caster", 3), ("big_drone", 1), ("elite_caster", 1)]
        else: enemies = [("elite", 2), ("elite_caster", 1), ("heavy", 4), ("boss", 1)]
        waves.append(WaveConfig(wave_num=i, enemies=enemies))
    return waves, mult
