"""卫戍协议 - Arcade UI (完全重写)"""
import math, random
from typing import Optional
import arcade

from copy import deepcopy
import sys, os
import winsound

# PyInstaller 打包后资源路径
def _asset(path):
    base = getattr(sys, '_MEIPASS', '')
    return os.path.join(base, path) if base else path

from .models import Operator, TriggerType, TraitType
from .data import ALL_PACTS, OPERATORS, STRATEGIES, generate_waves, ENEMIES
from .engine import GameState, PactLayerEngine, get_round_funds, get_shop_operators
from .map_gen import GameMap, CellType
from .logic import BattleLogic

_beep_enabled = True  # 战斗中关闭阻塞音效
def beep(freq=800, ms=80):
    if not _beep_enabled: return
    try: winsound.Beep(freq, min(ms, 10))
    except: pass

# ── BGM ──
bgm_player = None
bgm_current = None
bgm_main = bgm_battle = bgm_rest = None
try:
    bgm_main = arcade.load_sound(_asset('game/assets/main_bgm.wav'))
    bgm_battle = arcade.load_sound(_asset('game/assets/battle_bgm.wav'))
    bgm_rest = arcade.load_sound(_asset('game/assets/rest_bgm.wav'))
    sfx_leak = arcade.load_sound(_asset('game/assets/b_ui_alarmenter.wav'))
    sfx_dead = arcade.load_sound(_asset('game/assets/b_char_dead.wav'))
except Exception as e:
    print(f'BGM加载失败(可忽略): {e}')
    bgm_main = bgm_battle = bgm_rest = sfx_leak = sfx_dead = None

def play_sfx(sound):
    """播放一次性音效, 不打断BGM"""
    if sound:
        try: sound.play()
        except: pass

def play_bgm(sound):
    global bgm_player, bgm_current
    if sound is bgm_current: return  # 同一个BGM不重复播放
    bgm_current = sound
    try:
        if bgm_player:
            arcade.stop_sound(bgm_player)
        bgm_player = None
    except: pass
    if sound:
        try: bgm_player = sound.play(loop=True)
        except: pass

PACT_NAMES = {pid: p.name for pid, p in ALL_PACTS.items()}
PACT_OPS = {}  # pid -> [op names]
for op in OPERATORS:
    for pid in op.pacts:
        if pid not in PACT_OPS: PACT_OPS[pid] = []
        if op.name not in PACT_OPS[pid]: PACT_OPS[pid].append(op.name)

# ── 屏幕 ──
SW, SH = 1280, 720
TOP_H, SHOP_H = 48, 130
LEFT_W = 56
MAP_L, MAP_T = LEFT_W, TOP_H
MAP_W, MAP_H = SW - LEFT_W, SH - TOP_H - SHOP_H
CS = 68
COLS, ROWS = 14, 7
OX = MAP_L + (MAP_W - COLS * CS) // 2
OY = MAP_T + (MAP_H - ROWS * CS) // 2

# ── 设计系统: 颜色 (深色科幻风, Arknights-inspired) ──
# 基础
BG       = (12, 14, 18, 255)       # 最深背景
PANEL_BG = (22, 24, 30, 220)       # 面板半透明
CARD_BG  = (32, 36, 44, 240)       # 卡片背景
BUTTON_BG = (42, 48, 60, 230)      # 按钮背景

# 边框/分隔
BORDER   = (55, 60, 72, 200)
DIVIDER  = (45, 50, 62, 180)

# 文字
TEXT     = (225, 228, 235, 255)
DIM      = (140, 148, 160, 255)
WHITE    = (255, 255, 255, 255)

# 强调色
GOLD     = (252, 215, 65, 255)
RED      = (230, 60, 60, 255)
GREEN    = (60, 205, 85, 255)
BLUE     = (65, 130, 235, 255)
CYAN     = (65, 195, 210, 255)
PURPLE   = (175, 65, 220, 255)
YELLOW   = (255, 240, 40, 255)
ORANGE   = (245, 150, 40, 255)

# 悬停/选中
HOVER_BRIGHT = (80, 85, 100, 240)
HOVER_GLOW   = (100, 180, 255, 100)
SELECTED_BORDER = (252, 215, 65, 240)

# 游戏元素
C_PATH   = (145, 148, 155, 255)  # 路线
C_RANGED = (75, 155, 88, 255)   # 高台
C_WALL   = (185, 172, 105, 255) # 场外
C_SPAWN  = (195, 52, 52, 255)   # 红门
C_GOAL   = (52, 75, 195, 255)   # 蓝门

# 旧颜色别名(兼容)
PANEL = PANEL_BG
C_CARD = CARD_BG
C_BTN  = BUTTON_BG
C_HOV  = HOVER_BRIGHT
C_SEL  = (60, 55, 25, 240)

# ── 绘图wrapper ──
def rf(cx, cy, w, h, c):
    arcade.draw_lbwh_rectangle_filled(cx - w//2, cy - h//2, w, h, c)

def ro(cx, cy, w, h, c, bw=1):
    arcade.draw_lbwh_rectangle_outline(cx - w//2, cy - h//2, w, h, c, bw)

# ── 字体系统 ──
# 加载策略: 1.arcade.load_font(文件路径) 2.系统字体名 3.None(默认)
UI_FONT = None       # 主字体
UI_FONT_BOLD = None  # 粗体(标题)
NUM_FONT = None      # 数字等宽

def _try_load_font(paths, fallback=None):
    """尝试多种方式加载字体: 文件路径 → 系统字体名 → fallback"""
    for p in paths:
        try:
            resolved = _asset(p) if '/' in p else p
            name = arcade.load_font(resolved)
            if name:
                return name
        except Exception:
            pass
    return fallback

def _test_font_name(name):
    """测试系统字体名是否可用(不在窗口上下文中也可检测)"""
    try:
        t = arcade.Text('X', 0, 0, font_name=name)
        return True
    except Exception:
        return False

# 主字体
UI_FONT = _try_load_font([
    'game/assets/fonts/NotoSansSC-Regular.ttf',
    'game/assets/fonts/SourceHanSansSC-Regular.otf',
    'C:/Windows/Fonts/msyh.ttc',
])
if not UI_FONT:
    for sys_name in ['Microsoft YaHei', 'WenQuanYi Micro Hei', 'Noto Sans SC', 'SimHei']:
        if _test_font_name(sys_name):
            UI_FONT = sys_name
            break

# 粗体
UI_FONT_BOLD = _try_load_font([
    'game/assets/fonts/NotoSansSC-Bold.ttf',
    'game/assets/fonts/SourceHanSansSC-Bold.otf',
])
if not UI_FONT_BOLD:
    for sys_name in ['Microsoft YaHei', 'WenQuanYi Micro Hei', 'Noto Sans SC']:
        if _test_font_name(sys_name):
            UI_FONT_BOLD = sys_name
            break
    if not UI_FONT_BOLD:
        UI_FONT_BOLD = UI_FONT

# 数字等宽
NUM_FONT = _try_load_font([
    'game/assets/fonts/JetBrainsMono-Regular.ttf',
    'C:/Windows/Fonts/consola.ttf',
])
if not NUM_FONT:
    for sys_name in ['Consolas', 'Courier New', 'Lucida Console']:
        if _test_font_name(sys_name):
            NUM_FONT = sys_name
            break
    if not NUM_FONT:
        NUM_FONT = UI_FONT

# ── 字号系统 ──
FONT_TITLE = 32
FONT_H1    = 24
FONT_H2    = 18
FONT_BODY  = 14
FONT_SMALL = 11
FONT_TINY  = 9

# ── 文本缓存 (性能关键) ──
_text_cache = {}  # (text, size, font, color_hash) -> arcade.Text
def _get_cached_text(text, size, color, font_name):
    a = color[3] if len(color) > 3 else 255
    fn = font_name or ''
    key = (str(text), size, fn, color[0]*100000000+color[1]*100000+color[2]*1000+a)
    if key not in _text_cache:
        t = arcade.Text(str(text), 0, 0, color, size, anchor_x='center',
                        font_name=font_name or None)
        _text_cache[key] = t
    return _text_cache[key]

def txt(text, x, y, color=TEXT, size=14, anchor='center', max_w=0, font=None, bold=False):
    """统一文本绘制 - 缓存 + 截断 + 字体"""
    s = str(text)
    fs = min(size + 2, 32)
    fn = font or (UI_FONT_BOLD if bold else UI_FONT)
    # 截断
    if max_w > 0:
        chars = int(max_w / (fs * 0.62))
        if len(s) > chars:
            s = s[:chars-1] + '…'
    cached = _get_cached_text(s, fs, color, fn)
    cached.text = s
    if fn:
        cached.font_name = fn  # 确保字体正确(切换时更新)
    cached.x = x; cached.y = y
    cached.draw()
    return cached

# ── 按钮检测 ──
def hit(x, y, cx, cy, w, h):
    return cx-w//2 <= x <= cx+w//2 and cy-h//2 <= y <= cy+h//2

# ── UI组件 ──
def draw_panel(cx, cy, w, h, bg=PANEL_BG, border_color=BORDER, bw=1):
    """半透明面板 - 背景+柔和边框"""
    rf(cx, cy, w, h, bg)
    ro(cx, cy, w, h, border_color, bw)

def draw_card(cx, cy, w, h, hover=False, selected=False, tier_border=None):
    """卡片组件 - hover时高亮, selected时金边"""
    bg = HOVER_BRIGHT if hover else CARD_BG
    if selected:
        bg = (bg[0]+20, bg[1]+20, bg[2], bg[3]) if len(bg)==4 else (bg[0]+20, bg[1]+20, bg[2])
    rf(cx, cy, w, h, bg)

    if selected:
        ro(cx, cy, w, h, SELECTED_BORDER, 2)
    elif hover:
        ro(cx, cy, w, h, HOVER_GLOW, 2)
    elif tier_border:
        ro(cx, cy, w-2, h-2, tier_border, 1)

def draw_button(cx, cy, w, h, text, hover=False, color=BUTTON_BG, text_color=TEXT, size=14, accent=None):
    """按钮组件 - hover高亮, 点击反馈"""
    bg = HOVER_BRIGHT if hover else color
    rf(cx, cy, w, h, bg)
    border = accent if accent else (GOLD if hover else DIVIDER)
    bw = 2 if hover else 1
    ro(cx, cy, w, h, border, bw)
    # baseline anchoring使文字偏上, 所以把基线略微下移(half-height减去文字上升量)
    fs = size + 2
    ty = cy - (fs // 3)  # 下移约1/3字号补偿视觉偏上
    txt(text, cx, ty, text_color, size)

def tier_color(tier):
    """等阶→颜色"""
    if tier >= 6: return ORANGE
    if tier >= 5: return PURPLE
    if tier >= 3: return BLUE
    return DIM

def tier_badge(tier):
    """等阶→罗马数字"""
    return ['I','II','III','IV','V','VI'][min(tier-1, 5)]


class GarrisonWindow(arcade.Window):
    def __init__(self):
        super().__init__(SW, SH, '卫戍协议', resizable=False)
        self.state: Optional[GameState] = None
        self.gmap = GameMap(COLS, ROWS)
        self.waves, self.diff_mult = [], 1.0
        self.phase = 'setup'   # setup/decision/battle/rest/gameover
        self.strat_id = 's1'
        self.diff = '标准'

        # shop
        self.shop_ops: list[Operator] = []
        self.shop_owned: list[bool] = [False]*5  # 已购买标记
        self.center_lv = 1; self.temp_center_lv = 0
        self.center_upgrade_cost = 5
        self.frozen = False
        self.selected: Optional[Operator] = None
        self.deploy_dir = 0    # 0=右 1=上 2=左 3=下
        # 拖拽部署
        self.drag_op: Optional[Operator] = None   # 正在拖拽的干员
        self.drag_gx = self.drag_gy = -1           # 拖拽悬停的格子
        self.dir_mode = False                       # 方向选择模式
        self.dir_op: Optional[Operator] = None      # 方向模式中的干员
        self.dir_gx = self.dir_gy = -1              # 方向模式中的格子
        self.drag_mx = self.drag_my = 0             # 拖拽起始位置(屏幕坐标)

        # battle
        self.b_ops: list[dict] = []
        self.enemies: list[dict] = []
        self.b_killed = self.b_leaked = self.b_total = 0
        self.b_dp = 30; self.b_dp_tmr = 0.0
        self.b_speed = 1.0
        self.wave_q = []; self.wave_tmr = 0.0
        self.all_spawned = False
        self.dmg_nums: list = []; self.atk_lines: list = []

        self.rest_tmr = 0.0
        self.msg = ''; self.msg_tmr = 0.0
        self.hx = self.hy = -1
        self.decos = self._gen_decos()

        # 晋升奖励(显示在商店)
        self.promo_ops: list[Operator] = []
        self.gameover_timer = 0.0
        self._grid_drawn = False; self._grid_tex = None
        self.transition_alpha = 0.0; self.transition_msg = ""

        # 设置页
        self.setup_strat_idx = 0
        self.setup_diff_idx = 1

        play_bgm(bgm_main)  # 打开游戏即播放主界面BGM

    def _gen_decos(self):
        rng = random.Random(12345)  # 固定种子, 不会闪
        r = []
        for y in range(MAP_T+80, MAP_T+MAP_H-40, 80):
            w, h = rng.randint(20,38), rng.randint(30,55)
            r.append({'x':8, 'y':y, 'w':w, 'h':h, 'c':rng.choice([(55,60,70),(60,55,65),(50,60,55)])})
        return r

    # ── setup ───────────────────────────────────────
    def _start_game(self):
        strat = STRATEGIES[self.setup_strat_idx]
        diffs = ['入门','标准','险境','绝境','终极']
        self.diff = diffs[self.setup_diff_idx]
        self.state = GameState(life=strat.hp, difficulty=self.diff, strategy=strat)
        self.gmap.generate()
        self.waves, self.diff_mult = generate_waves(self.diff)
        self.state.total_waves = len(self.waves)
        self.state.round_num = 1
        self.center_lv = 1; self.center_upgrade_cost = 5
        self.shop_owned = [False]*5
        self.frozen = False; self.selected = None
        self._give_funds(); self._refresh_shop()
        # s6: 开局获得随机VI阶干员
        if strat.id == 's6':
            t6 = [op for op in OPERATORS if op.tier == 6]
            if t6:
                gift = deepcopy(random.choice(t6))
                import uuid as _u3; gift.uid = str(_u3.uuid4())[:8]
                self.state.roster.append(gift); self.state.bench.append(gift)
                self.msg = f'优等生: 获得{gift.name}!'
            else:
                self.msg = '优等生: 无可用VI阶干员'
        else:
            self.msg = ''
        self.msg = self.msg or f'第1回合 · {strat.name} · {self.diff}'; self.msg_tmr = 3.0

    def _give_funds(self):
        base = get_round_funds(self.state)
        # s4: 额外获得持有资金的10%向上取整
        if self.state.strategy.id == 's4':
            interest = max(1, (self.state.funds * 10 + 99) // 100)
            base += interest
        self.state.funds += base

    def _refresh_shop(self):
        # 按调度中心等级筛选
        import uuid as _uuid
        all_ops = []
        clv = max(self.center_lv, self.temp_center_lv)
        for op in OPERATORS:
            if op.tier <= clv:
                cp = deepcopy(op); cp.uid = str(_uuid.uuid4())[:8]; all_ops.append(cp)
        if len(all_ops) < 5:
            for op in OPERATORS:
                cp = deepcopy(op); cp.uid = str(_uuid.uuid4())[:8]; all_ops.append(cp)
        self.shop_ops = random.sample(all_ops, min(5, len(all_ops)))
        self.shop_owned = [False]*5

    def _check_promotion(self):
        from collections import Counter
        cnt = Counter()
        for op in self.state.roster:
            if not op.is_elite:
                cnt[op.id] += 1
        for type_id, n in list(cnt.items()):
            if n < 3: continue
            # 收集要晋升的3个干员uid
            uids = []
            for op in self.state.bench:
                if op.id == type_id and not op.is_elite and len(uids)<3:
                    uids.append(op.uid)
            for op in self.state.deployed:
                if op.id == type_id and not op.is_elite and len(uids)<3:
                    uids.append(op.uid)
            if len(uids) < 3: continue

            # 通过uid从各列表精确移除
            for uid in uids:
                for lst in [self.state.bench, self.state.deployed, self.state.roster]:
                    for i, op in enumerate(lst):
                        if op.uid == uid:
                            lst.pop(i); break
                for x in range(COLS):
                    for y in range(ROWS):
                        c = self.gmap.get_cell(x,y)
                        if c and c.operator_id == uid:
                            c.occupied = False; c.operator_id = ""

            # 找到模板创建精锐
            template = next((op for op in OPERATORS if op.id == type_id), None)
            if not template: continue

            elite = Operator(id=template.id, name=template.name, tier=template.tier,
                cost=template.cost, pacts=list(template.pacts), traits=list(template.traits),
                is_elite=True, base_hp=template.base_hp, base_atk=template.base_atk,
                base_def=template.base_def, atk_speed=template.atk_speed,
                block_count=template.block_count)
            self.state.roster.append(elite); self.state.bench.append(elite)
            self.msg = f'晋升! {elite.name} → [精锐]'; self.msg_tmr = 3.0

            # 晋升奖励: 3张免费卡加入promo_ops(显示在商店)
            import uuid as _u2
            candidates = []
            for op in OPERATORS:
                if op.tier == self.center_lv and op.id != type_id:
                    cp = deepcopy(op); cp.uid = str(_u2.uuid4())[:8]; cp.cost = 0; candidates.append(cp)
            if len(candidates) >= 3:
                self.promo_ops = random.sample(candidates, 3)
            else:
                self.promo_ops = [deepcopy(op) for op in random.sample(OPERATORS, min(3, len(OPERATORS)))]
                for cp in self.promo_ops: cp.uid = str(_u2.uuid4())[:8]; cp.cost = 0
            self.msg = f'晋升奖励! 在商店选择1名免费干员'; self.msg_tmr = 4.0
            break

    # ── actions ─────────────────────────────────────
    def buy(self, idx):
        if idx < 0 or idx >= len(self.shop_ops): return
        if self.shop_owned[idx]: return
        op = self.shop_ops[idx]
        if self.state.funds < op.cost: self.msg='资金不足!'; self.msg_tmr=1.5; return
        self.state.funds -= op.cost
        op = deepcopy(op)
        op.uid = str(__import__('uuid').uuid4())[:8]  # 强制新uid确保唯一
        self.state.roster.append(op); self.state.bench.append(op)
        self.shop_owned[idx] = True
        beep(600, 60)
        PactLayerEngine.trigger_obtain(self.state, op)
        # 策略: 御守之力(s7) - 额外触发
        if self.state.strategy.id == 's7':
            PactLayerEngine.trigger_obtain(self.state, op)
        # PREP特质: 根据描述分发效果
        for t in op.traits:
            if t.trait_type == TraitType.PREP and t.trigger == TriggerType.ON_OBTAIN:
                td = t.description; n = 2 if op.is_elite else 1
                if '刷新' in td:
                    self.state.free_refreshes = getattr(self.state, 'free_refreshes', 0) + n
                    self.msg = f'获得{n}次免费刷新!'; self.msg_tmr = 2.0
                elif '资金' in td:
                    self.state.funds += n * 2
                    self.msg = f'获得{n*2}资金!'; self.msg_tmr = 2.0
                elif '调度中心' in td:
                    self.temp_center_lv = min(6, self.center_lv + 1)
                    self.msg = '调度中心临时+1级!'; self.msg_tmr = 2.0
                elif '升级中心' in td:
                    self.center_upgrade_cost = max(1, self.center_upgrade_cost - 2)
                    self.msg = '升级费用-2!'; self.msg_tmr = 2.0
        # 投资人: 更新激活状态(整备区新干员可能激活投资人或叠加计数)
        PactLayerEngine.update_activation(self.state)
        inv = self.state.pact_states.get('investor')
        if inv and inv.active:
            for _ in range((3 if inv.layers>=100 else 2)-1):
                PactLayerEngine.trigger_obtain(self.state, op)
        self._check_promotion()
        self.msg = f'获得 {op.name}'; self.msg_tmr = 1.5

    def refresh_shop(self):
        free = False
        # 免费刷新次数(普罗旺斯等)
        fr = getattr(self.state, 'free_refreshes', 0)
        if fr > 0:
            self.state.free_refreshes = fr - 1
            free = True
        # 远见: 刷新时有概率免费
        if not free:
            foresight = self.state.pact_states.get('foresight')
            if foresight and foresight.active:
                chance = (18 + 0.3 * foresight.layers) / 100.0
                if random.random() < chance:
                    free = True
        if not free:
            if self.state.funds < self.state.refresh_cost:
                self.msg = '资金不足!'; self.msg_tmr = 1.0; return
            self.state.funds -= self.state.refresh_cost
        PactLayerEngine.trigger_refresh(self.state)
        self._refresh_shop()
        self.msg = '免费刷新!' if free else '刷新!'; self.msg_tmr = 1.0

    def sell(self, op):
        price = max(1, op.cost//2); self.state.funds += price
        for lst in [self.state.bench, self.state.deployed, self.state.roster]:
            if op in lst: lst.remove(op)
        PactLayerEngine.trigger_trait(self.state, TriggerType.ON_SELL, op)
        PactLayerEngine.update_activation(self.state)
        self.msg = f'出售 {op.name} +${price}'; self.msg_tmr = 1.5

    def deploy(self, op, gx, gy):
        if self.phase != 'decision':
            self.msg = '只能在整备阶段部署!'; self.msg_tmr = 1.5; return False
        if self.b_dp < op.deploy_cost:
            self.msg = f'DP不足! 需{op.deploy_cost}'; self.msg_tmr = 1.5; return False
        cell = self.gmap.get_cell(gx, gy)
        if not cell or cell.occupied: return False
        is_melee = op.block_count > 0
        if not self.gmap.can_deploy(gx, gy, is_melee):
            self.msg = '无法在此部署!'; self.msg_tmr = 1.0; return False
        if len(self.state.deployed) >= self.state.max_operators:
            self.msg = f'部署位已满({len(self.state.deployed)}/{self.state.max_operators})!'; self.msg_tmr = 1.5; return False
        if self.phase == 'battle': self.b_dp -= op.deploy_cost
        cell.occupied = True; cell.operator_id = op.uid
        if op in self.state.bench: self.state.bench.remove(op)
        if op not in self.state.deployed: self.state.deployed.append(op)
        PactLayerEngine.trigger_deploy(self.state, op)
        PactLayerEngine.update_activation(self.state)
        beep(1000, 50)
        self.msg = f'部署 {op.name}'; self.msg_tmr = 1.0
        if self.phase == 'battle':
            self.b_ops.append({'op':op,'gx':gx,'gy':gy,
                'hp':int(op.hp*self._hp_m(op)),'max_hp':int(op.hp*self._hp_m(op)),
                'atk':int(op.atk*self._atk_m(op)),'def':op.defense,
                'timer':0.0,'alive':True,'range':self._calc_range(gx,gy,op)})
        return True

    def retreat(self, gx, gy):
        if self.phase != 'decision': self.msg='只能在整备阶段撤退!'; self.msg_tmr=1.5; return
        cell = self.gmap.get_cell(gx, gy)
        if not cell or not cell.occupied: return
        ouid = cell.operator_id; cell.occupied=False; cell.operator_id=""
        for op in self.state.deployed[:]:
            if op.uid == ouid:
                self.state.deployed.remove(op); self.state.bench.append(op)
                if self.phase=='battle': self.b_dp=min(99,self.b_dp+int(op.deploy_cost*0.5))
                break
        self.b_ops = [b for b in self.b_ops if not (b['gx']==gx and b['gy']==gy)]
        PactLayerEngine.update_activation(self.state)
        self.msg='撤退'; self.msg_tmr=1.0

    def _atk_m(self, op):
        m = 1.0
        # 策略加成
        if self.state and self.state.strategy:
            if self.state.strategy.id == 's5':  # 以己之长
                m *= 1.20
            elif self.state.strategy.id == 's2':  # 众志合一
                n = sum(1 for ps in self.state.pact_states.values() if ps.active)
                if n >= 5: m *= 1.40
                elif n >= 4: m *= 1.30
                elif n >= 3: m *= 1.20
        for pid, ps in self.state.pact_states.items():
            if not ps.active:
                continue
            layers = ps.layers
            # 只对拥有该盟约的干员生效
            has = pid in op.pacts
            if pid == 'yan' and has:
                m *= 1.0 + (23 + 0.9 * layers) / 100.0
            elif pid == 'kazimierz' and has:
                m *= 1.0 + (50 + layers) / 100.0
            elif pid == 'precision' and has:
                m *= 1.0 + (10 + 1.2 * layers) / 100.0
            elif pid == 'assault' and has:
                m *= 1.0 + (25 + layers) / 100.0
            elif pid == 'kjerag' and has:
                m *= 1.0 + 0.25 + 0.01 * layers
            elif pid == 'victoria' and has:
                m *= 1.0 + 0.25 + 0.008 * layers
            elif pid == 'sargon' and has:
                m *= 1.0 + (50 + layers) / 100.0
            elif pid == 'siracusa' and has:
                m *= 1.0 + (15 + 0.4 * layers) / 100.0
            elif pid == 'laterano' and has:
                m *= 1.0 + (20 + 0.5 * layers) / 100.0
            elif pid == 'solo' and has:
                n = sum(1 for b in self.b_ops if b.get('alive', True) and 'solo' in b['op'].pacts)
                if n < 1: m *= 1.6  # 自己还未加入b_ops, 在场其他solo=0才生效
            elif pid == 'aegir' and has:
                m *= 1.0 + (35 + layers) * 0.75 / 100.0
            elif pid == 'arcane' and has:
                m *= 1.0 + (20 + layers) / 100.0
        return m

    def _hp_m(self, op):
        m = 1.0
        for pid, ps in self.state.pact_states.items():
            if not ps.active: continue
            layers = ps.layers; has = pid in op.pacts
            if pid == 'aegir' and has: m *= 1.0 + (35 + layers) / 100.0
            elif pid == 'fortification' and has: m *= 1.0 + (25 + 1.2 * layers) / 100.0
            elif pid == 'assault' and has: m *= 1.0 + (25 + layers) / 100.0
            elif pid == 'solo' and has:
                n = sum(1 for b in self.b_ops if b.get('alive', True) and 'solo' in b['op'].pacts)
                if n < 1: m *= 1.6
            # 核心盟约同时加成HP(减半)
            elif pid == 'yan' and has: m *= 1.0 + (23 + 0.9 * layers) / 200.0
            elif pid == 'kazimierz' and has: m *= 1.0 + (50 + layers) / 200.0
            elif pid == 'kjerag' and has: m *= 1.0 + 0.12 + 0.005 * layers
            elif pid == 'victoria' and has: m *= 1.0 + 0.12 + 0.004 * layers
            elif pid == 'sargon' and has: m *= 1.0 + (50 + layers) / 200.0
            elif pid == 'siracusa' and has: m *= 1.0 + (15 + 0.4 * layers) / 200.0
            elif pid == 'laterano' and has: m *= 1.0 + (20 + 0.5 * layers) / 200.0
            elif pid == 'precision' and has: m *= 1.0 + (10 + 1.2 * layers) / 200.0
        return m

    def _aspd_bonus(self, op):
        """攻击速度加成(含盟约+特质)"""
        b = 0.0
        for pid, ps in self.state.pact_states.items():
            if not ps.active: continue
            layers = ps.layers
            has = pid in op.pacts
            if pid == 'agility' and has:
                b += 15 + layers + (50 if layers >= 40 else 0)
            elif pid == 'assault' and has and layers >= 50:
                b += 50
            elif pid == 'sargon' and has:
                b += 50
            elif pid == 'laterano' and has:
                b += 30
            elif pid == 'siracusa' and has:
                b += 50
            elif pid == 'victoria' and has:
                # 焰影苇草等: 每叠3层攻速+2
                b += (layers // 3) * 2
        # 隐现特质: 拉特兰每叠5层攻速+2
        if 'laterano' in op.pacts:
            ls = self.state.pact_states.get('laterano')
            if ls and ls.active: b += (ls.layers // 5) * 2
        return b

    def _def_m(self, op):
        """防御加成"""
        m = 1.0
        for pid, ps in self.state.pact_states.items():
            if not ps.active: continue
            layers = ps.layers
            if pid == 'assistance' and pid in op.pacts:
                m *= 1.0 + (15 + 1.2 * layers) / 100.0
        return m

    def _dmg_reduction(self):
        return 0.0

    def _calc_range(self, gx, gy, op):
        cells = []
        dirs = [(1,0),(0,1),(-1,0),(0,-1)]
        dx, dy = dirs[self.deploy_dir]
        if op.block_count > 0:
            for r in [0,1,2]:
                tx, ty = gx+dx*r, gy+dy*r
                if 0<=tx<COLS and 0<=ty<ROWS: cells.append((tx,ty))
        else:
            for r in range(1,5):
                for s in range(-1,2):
                    tx, ty = gx+dx*r+dy*s, gy+dy*r+dx*s
                    if 0<=tx<COLS and 0<=ty<ROWS: cells.append((tx,ty))
        return cells

    # ── battle ──────────────────────────────────────
    def start_battle(self):
        if not self.state.deployed: self.msg='请至少部署1名干员!'; self.msg_tmr=2.0; return
        self.phase='battle'; self.b_dp=30; self.b_dp_tmr=0.0
        global _beep_enabled; _beep_enabled = False  # 战斗中禁用阻塞音效
        play_bgm(bgm_battle)
        self.b_killed=self.b_leaked=0; self.b_speed=1.0; self.wave_tmr=0.0
        self.all_spawned=False; self.dmg_nums.clear(); self.atk_lines.clear()
        self.b_ops.clear()
        for op in self.state.deployed:
            for x in range(COLS):
                for y in range(ROWS):
                    c=self.gmap.get_cell(x,y)
                    if c and c.occupied and c.operator_id==op.uid:
                        _, aspd_val = BattleLogic.calc_aspd(self.state, op)
                        effective_speed = op.atk_speed * (100.0 / (100.0 + max(0, aspd_val)))
                        bo = {'op':op,'gx':x,'gy':y,
                            'hp':int(op.hp*BattleLogic.calc_hp_mult(self.state,op,self.b_ops)),
                            'max_hp':int(op.hp*BattleLogic.calc_hp_mult(self.state,op,self.b_ops)),
                            'atk':int(op.atk*BattleLogic.calc_atk_mult(self.state,op,self.b_ops)),
                            'def':int(op.defense*BattleLogic.calc_def_mult(self.state,op)),
                            'timer':0.0,'alive':True,'range':self._calc_range(x,y,op),
                            'atk_spd':effective_speed}
                        BattleLogic.apply_trait_effects(op, bo, self.state)
                        self.b_ops.append(bo)
                        break
        wi = self.state.round_num-1
        self.wave_q = []
        if wi < len(self.waves):
            for eid, cnt in self.waves[wi].enemies:
                t = ENEMIES.get(eid)
                if t:
                    # 随波次递增: 每波+15%HP, +10%ATK
                    wave_scale = 1.0 + (wi * 0.06)
                    for _ in range(cnt):
                        self.wave_q.append({'id':eid,'name':t.name,
                            'hp':int(t.hp*self.diff_mult*wave_scale),
                            'max_hp':int(t.max_hp*self.diff_mult*wave_scale),
                            'atk':int(t.atk*self.diff_mult*wave_scale),
                            'def':int(t.defense*wave_scale),
                            'speed':t.speed*60,'is_boss':t.is_boss,'is_elite':t.is_elite})
        self.b_total=len(self.wave_q); self.enemies.clear()
        PactLayerEngine.trigger_combat_start(self.state)
        PactLayerEngine.update_activation(self.state)
        # 策略: 重点监护(s1) - 每等阶+2层
        if self.state.strategy.id == 's1':
            seen_tiers = set()
            for op in self.state.deployed:
                if op.tier not in seen_tiers:
                    seen_tiers.add(op.tier)
                    for pid in op.pacts:
                        if pid in self.state.pact_states:
                            self.state.pact_states[pid].layers += 2
            self.msg = f'重点监护: {len(seen_tiers)}个等阶各+2层!'; self.msg_tmr = 2.0
        # 策略: 众志合一(s2) - 按激活盟约数加成(已在_atk_m中处理)
        # 策略: 以己之长(s5) - 全员+20%攻击力
        if self.state.strategy.id == 's5':
            self.msg = '以己之长: 全员攻击力+20%'; self.msg_tmr = 2.0

        beep(400, 200)
        self.msg = self.msg or '战斗开始!'; self.msg_tmr = max(self.msg_tmr, 2.0)

    def _update_battle(self, dt):
        rd = dt * self.b_speed
        steps = min(max(1, int(rd / 0.04)), 8)  # 上限防死亡螺旋
        sub_dt = rd / steps
        for _ in range(steps):
            self._battle_step(sub_dt)
            if self.phase != 'battle': return  # 战斗结束立即退出

    def _battle_step(self, rd):
        self.b_dp_tmr += rd
        while self.b_dp_tmr >= 1.0: self.b_dp_tmr -= 1.0; self.b_dp = min(99, self.b_dp+1)
        self.wave_tmr += rd
        if self.wave_q and self.wave_tmr >= 2.5:
            self.wave_tmr = 0.0
            d = self.wave_q.pop(0)
            # 从右侧(红门)出生: path[-1]是最右格
            pc = self.gmap.path_cells
            if pc:
                sc = pc[-1]
                self.enemies.append({**d, 'x':OX+sc[0]*CS+CS//2, 'y':OY+sc[1]*CS+CS//2,
                    'alive':True, 'blocked_by':None, 'timer':1.5, 'path_idx': len(pc)-1})
        if not self.wave_q and not self.enemies: self.all_spawned=True
        for e in self.enemies:
            if not e['alive']: continue
            if e.get('blocked_by') is not None:
                bl = e['blocked_by']
                if bl['alive']:
                    e['timer'] -= rd
                    if e['timer'] <= 0:
                        e['timer'] = 1.5
                        dmg = max(int(e['atk']*0.15), e['atk']-bl.get('def',0))
                        dmg = int(dmg * (1.0 - self._dmg_reduction()))
                        bl['hp'] -= dmg
                        self.dmg_nums.append((bl['gx']*CS+OX+CS//2, bl['gy']*CS+OY+10, str(dmg), 1.0, RED))
                        if bl['hp']<=0:
                            bl['alive']=False; e['blocked_by']=None
                            base_timer = bl['op'].redeploy_time
                            # 突袭盟约: 减再部署时间
                            assault_ps = self.state.pact_states.get('assault')
                            if assault_ps and assault_ps.active and 'assault' in bl['op'].pacts:
                                reduction = (25 + 0.2 * assault_ps.layers) / 100.0
                                base_timer = int(base_timer * (1.0 - min(reduction, 0.8)))
                            bl['death_timer'] = max(5, base_timer)
                            play_sfx(sfx_dead)
                            # 不屈: 概率立即复活
                            indom = self.state.pact_states.get('indomitable')
                            if indom and indom.active and 'indomitable' in bl['op'].pacts:
                                if random.random() < (18+0.4*indom.layers)/100.0:
                                    bl['alive']=True; bl['hp']=int(bl['max_hp']*0.5)
                                    if 'death_timer' in bl: del bl['death_timer']
                                    self.msg=f'{bl["op"].name} 不屈!'; self.msg_tmr=1.5
                else: e['blocked_by'] = None
            else:
                pc = self.gmap.path_cells
                pid = e.get('path_idx', len(pc)-1)
                # 到达最左(蓝门)?
                if pid <= 0:
                    e['alive'] = False
                    self.b_leaked += 1
                    play_sfx(sfx_leak)
                    if self.b_leaked <= 3: self.msg = f'漏怪!(-{self.b_leaked}HP)'; self.msg_tmr = 1.5
                    continue
                # 向左移动: path_idx递减
                target_pid = pid - 1
                tx, ty = pc[target_pid]
                tpx, tpy = OX + tx*CS + CS//2, OY + ty*CS + CS//2
                dx, dy = tpx - e['x'], tpy - e['y']
                dist = math.hypot(dx, dy)
                if dist < 4:
                    e['x'], e['y'] = tpx, tpy
                    e['path_idx'] = target_pid
                else:
                    spd = e['speed'] * rd
                    e['x'] += (dx / dist) * spd
                    e['y'] += (dy / dist) * spd

                egx, egy = int((e['x']-OX)//CS), int((e['y']-OY)//CS)
                for bo in self.b_ops:
                    if not bo['alive'] or bo['op'].block_count<=0: continue
                    if bo['gx']==egx and bo['gy']==egy:
                        bc = sum(1 for ee in self.enemies if ee.get('blocked_by')==bo and ee['alive'])
                        if bc < bo['op'].block_count: e['blocked_by']=bo; break
        # 每帧特效(HP流失/回复)
        for bo in self.b_ops:
            BattleLogic.process_tick(bo, rd)
        BattleLogic.process_global_regen(self.b_ops, rd)
        # 死亡干员复活计时
        for bo in self.b_ops:
            if not bo['alive'] and 'death_timer' in bo:
                bo['death_timer'] -= rd
                if bo['death_timer'] <= 0:
                    bo['alive'] = True; bo['hp'] = bo['max_hp']
                    del bo['death_timer']
                    self.msg = f'{bo["op"].name} 复活!'; self.msg_tmr = 1.5
        for bo in self.b_ops:
            if not bo['alive']: continue
            bo['timer'] -= rd
            if bo['timer'] > 0: continue
            op_px = OX+bo['gx']*CS+CS//2; op_py = OY+bo['gy']*CS+CS//2

            # 奶妈: 治疗范围内血量最低的友方
            if bo['op'].healer:
                result = BattleLogic.process_healer(bo, self.b_ops, OX, OY, CS)
                if result:
                    heal, tx, ty = result
                    bo['timer'] = bo.get('atk_spd', bo['op'].atk_speed)
                    self.atk_lines.append((op_px, op_py, tx, ty, 0.3))
                    self.dmg_nums.append((tx, ty-15, '+'+str(heal), 1.0, BLUE))
                continue

            # 常规攻击
            best = None
            for e in self.enemies:
                if not e['alive']: continue
                egx, egy = int((e['x']-OX)//CS), int((e['y']-OY)//CS)
                dist = math.hypot(e['x']-op_px, e['y']-op_py)
                in_range = (egx,egy) in bo['range'] or e.get('blocked_by')==bo or dist < 150
                if in_range:
                    if best is None or e['x'] < best['x']: best = e
            if best:
                bo['timer'] = bo.get('atk_spd', bo['op'].atk_speed)
                raw = bo['atk']
                if bo['op'].id in ('angel','excu','saint_angel') and best.get('id')=='drone': raw*=2
                enemy_def = best.get('def', 0)
                if self.state.strategy.id == 's5':
                    enemy_def = int(enemy_def * 0.75)
                dmg = max(int(raw*0.05), raw - enemy_def)
                best['hp'] -= dmg
                beep(1200, 15)
                self.atk_lines.append((op_px,op_py, best['x'], best['y'], 0.2))
                self.dmg_nums.append((best['x'], best['y']-15, str(dmg), 1.0, GOLD))
                if best['hp']<=0: best['alive']=False; best['blocked_by']=None; self.b_killed+=1
                if best.get('is_boss'): beep(200, 300)
        self.enemies = [e for e in self.enemies if e['alive']]
        self.b_ops = [b for b in self.b_ops if b['alive'] or 'death_timer' in b]
        self.dmg_nums = [(x,y,t,tt-rd,c) for x,y,t,tt,c in self.dmg_nums if tt-rd>0]
        self.atk_lines = [(a,b,c,d,tt-rd) for a,b,c,d,tt in self.atk_lines if tt-rd>0]
        if self.all_spawned and not self.enemies: self._end_battle()

    def _end_battle(self):
        self.phase='rest'; self.rest_tmr=0.0
        global _beep_enabled; _beep_enabled = True  # 恢复音效
        play_bgm(bgm_rest)
        # 清除战斗特效
        self.dmg_nums.clear(); self.atk_lines.clear()
        if self.b_leaked>0: self.state.life -= self.b_leaked
        if self.state.life<=0: self.phase='gameover'; return
        # 被击倒且无复活计时的干员回整备区, 等待复活的留在场上
        for bo in self.b_ops:
            if not bo['alive'] and 'death_timer' not in bo:
                op=bo['op']
                if op in self.state.deployed: self.state.deployed.remove(op); self.state.bench.append(op)
                PactLayerEngine.trigger_defeat(self.state, op)
                for x in range(COLS):
                    for y in range(ROWS):
                        c=self.gmap.get_cell(x,y)
                        if c and c.operator_id==op.uid: c.occupied=False; c.operator_id=""
        PactLayerEngine.trigger_rest_start(self.state); PactLayerEngine.trigger_rest_end(self.state)
        self.msg=f'回合结束! 击杀{self.b_killed}/{self.b_total}'; self.msg_tmr=3.0

    def _next_round(self):
        self.state.round_num+=1
        if self.state.round_num>self.state.total_waves: self.phase='gameover'; return
        # 不更换地图, 保留干员位置
        self.phase='decision'
        play_bgm(bgm_rest)
        self._give_funds()
        if not self.frozen: self._refresh_shop()
        self.selected=None; self.drag_op=None; self.dir_mode=False; self.dir_op=None
        if self.state.round_num in (5,10,13): self.center_lv=min(6,self.center_lv+1)
        # s1: 每回合已激活盟约层数+8
        if self.state.strategy.id == 's1':
            for ps in self.state.pact_states.values():
                if ps.active: ps.layers += 8
            self.msg = '重点监护: 每个已激活盟约+8层!'; self.msg_tmr = 2.0
        # s8: 文火慢炖 T8触发
        if self.state.strategy.id == 's8' and self.state.round_num == 8:
            active = [ps for ps in self.state.pact_states.values() if ps.active]
            if len(active) == 1:
                active[0].layers += 36
                self.msg = f'文火慢炖: 【{active[0].pact.name}】+36层!'
            elif active:
                for ps in active: ps.layers += 12
                self.msg = f'文火慢炖: 每个已激活盟约+12层!'
            self.msg_tmr = 3.0
        if not self.msg or self.msg_tmr <= 0:
            self.msg = f'第{self.state.round_num}回合! 调度Lv.{self.center_lv}'; self.msg_tmr = 2.0

    # ── arcade callbacks ────────────────────────────
    def on_update(self, dt):
        if self.transition_alpha > 0: self.transition_alpha = max(0, self.transition_alpha - dt*1.2)
        if self.phase=='battle': self._update_battle(dt)
        elif self.phase=='rest':
            self.rest_tmr+=dt
            if self.rest_tmr>2.0: self._next_round()
        elif self.phase=='gameover':
            self.gameover_timer += dt
            if self.gameover_timer > 10.0:
                self.close()
        if self.msg_tmr>0: self.msg_tmr-=dt

    def on_mouse_motion(self, x, y, dx, dy):
        self.hx, self.hy = x, y
        # 方向选择模式: 实时根据鼠标位置更新方向
        if self.dir_mode and self.dir_op:
            cx = OX + self.dir_gx*CS + CS//2
            cy = OY + self.dir_gy*CS + CS//2
            mx, my = x - cx, y - cy
            if abs(mx) > 15 or abs(my) > 15:
                if abs(mx) > abs(my):
                    self.deploy_dir = 0 if mx > 0 else 2  # 右/左
                else:
                    self.deploy_dir = 1 if my > 0 else 3  # 上/下

    def on_mouse_press(self, x, y, button, modifiers):
        if self.phase == 'setup':
            self._click_setup(x, y); return
        if self.phase == 'gameover':
            self.close(); return

        if button == arcade.MOUSE_BUTTON_RIGHT:
            self._right_click(x, y); return
        if button != arcade.MOUSE_BUTTON_LEFT: return

        # 退出
        if hit(x, y, 27, MAP_T+26, 44, 36): self.close(); return

        # 方向选择模式: 点击地图确认部署
        if self.dir_mode and self.dir_op:
            if OX<=x<=OX+COLS*CS and OY<=y<=OY+ROWS*CS:
                self.deploy(self.dir_op, self.dir_gx, self.dir_gy)
                self.dir_mode = False; self.dir_op = None
                self.selected = None
                return
            # 点击地图外不处理, 继续往下(可能是点商店按钮)

        # 地图点击
        if OX<=x<=OX+COLS*CS and OY<=y<=OY+ROWS*CS:
            gx, gy = int((x-OX)//CS), int((y-OY)//CS)
            cell = self.gmap.get_cell(gx, gy)
            if cell and cell.occupied and self.phase=='battle':
                for bo in self.b_ops:
                    if bo['gx']==gx and bo['gy']==gy:
                        self.msg=f"{bo['op'].name} HP:{bo['hp']}/{bo['max_hp']}"; self.msg_tmr=2.0; break
            return

        # 晋升奖励商店(免费) - 与绘制位置对齐
        if self.promo_ops:
            py2 = SH-SHOP_H-20
            for i, op in enumerate(self.promo_ops):
                if MAP_L+100+i*140<=x<=MAP_L+100+i*140+130 and py2-60<=y<=py2:
                    if self.phase=='decision':
                        op2 = deepcopy(op)
                        op2.uid = str(__import__('uuid').uuid4())[:8]
                        # 恢复原始cost(晋升奖励显示为0, 但售卖应用原价)
                        tmpl = next((o for o in OPERATORS if o.id == op.id), None)
                        op2.cost = tmpl.cost if tmpl else op.cost
                        self.state.roster.append(op2); self.state.bench.append(op2)
                        PactLayerEngine.trigger_obtain(self.state, op2)
                        self._check_promotion()
                        self.msg = f'晋升奖励: {op2.name}!'; self.msg_tmr = 2.0
                        self.promo_ops = []
                    return

        # 商店
        sy = SH-SHOP_H+80; sx = MAP_L+100
        for i in range(5):
            if sx+i*140<=x<=sx+i*140+130 and sy-5<=y<=sy+53:
                if self.phase=='decision': self.buy(i)
                return

        # 底部按钮行(从右往左: 资金→刷新→冻结; 升级在左侧)
        by = SH-SHOP_H+16
        if self.phase=='decision':
            rx = SW - 20
            funds = f'${self.state.funds}'
            est_funds_w = len(funds) * 14
            rx -= est_funds_w + 10
            if hit(x, y, rx-35, by, 70, 28):
                self.refresh_shop(); beep(800, 60); return
            rx -= 78
            if hit(x, y, rx-35, by, 70, 28):
                self.frozen = not self.frozen; beep(500, 80)
                self.msg = '已冻结商店' if self.frozen else '已解冻'; self.msg_tmr=1.5; return
        if hit(x, y, MAP_L+65, by, 72, 28) and self.phase=='decision':
            if self.state.funds >= self.center_upgrade_cost and self.center_lv < 6:
                self.state.funds -= self.center_upgrade_cost
                self.center_lv += 1
                self.center_upgrade_cost = self.center_lv * 5
                self.msg = f'调度中心升级! Lv.{self.center_lv}'; self.msg_tmr = 2.0
            else: self.msg = '资金不足或已满级'; self.msg_tmr = 1.5
            return
        # 开始战斗
        if self.phase=='decision' and hit(x, y, SW-70, SH-SHOP_H+SHOP_H-20, 100, 32):
            self.start_battle(); return
        # 倍速
        if self.phase=='battle':
            for i, sp in enumerate([1,2,5,8]):
                bx = MAP_L+320+i*75
                if hit(x, y, bx, by, 68, 32):
                    self.b_speed = sp
                    self.msg = f'速度: {sp}x'; self.msg_tmr = 1.0
                    return

        # 整备区: 点击开始拖拽
        bench_y = SH-SHOP_H+34
        if bench_y<=y<=bench_y+44 and MAP_L+100<=x:
            idx = int((x-MAP_L-100)//72)
            if 0<=idx<len(self.state.bench):
                self.drag_op = self.state.bench[idx]
                self.selected = self.drag_op
                self.drag_mx, self.drag_my = x, y
                self.msg = f'拖拽 {self.drag_op.name} 到地图格子'; self.msg_tmr = 3.0

    def on_mouse_release(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT: return
        # 拖拽干员到地图
        if self.drag_op:
            op = self.drag_op; self.drag_op = None
            if OX<=x<=OX+COLS*CS and OY<=y<=OY+ROWS*CS:
                gx, gy = int((x-OX)//CS), int((y-OY)//CS)
                cell = self.gmap.get_cell(gx, gy)
                is_melee = op.block_count > 0
                if cell and not cell.occupied and self.gmap.can_deploy(gx, gy, is_melee):
                    if len(self.state.deployed) >= self.state.max_operators:
                        self.msg = f'部署位已满({len(self.state.deployed)}/{self.state.max_operators})!'; self.msg_tmr = 1.5
                        self.selected = None; return
                    # 进入方向选择模式
                    self.dir_mode = True
                    self.dir_op = op
                    self.dir_gx, self.dir_gy = gx, gy
                    self.deploy_dir = 0
                    self.msg = f'拖拽选择方向 (→↑←↓) · 点击确认 · ESC取消'; self.msg_tmr = 5.0
                    return
                else:
                    self.msg = '无法在此部署!'; self.msg_tmr = 1.0
            self.selected = None

    def _right_click(self, x, y):
        """右键: 出售/撤退"""
        # 地图上右键撤退
        if OX<=x<=OX+COLS*CS and OY<=y<=OY+ROWS*CS:
            gx, gy = int((x-OX)//CS), int((y-OY)//CS)
            self.retreat(gx, gy); return
        # 整备区右键出售
        bench_y = SH-SHOP_H+34
        if bench_y<=y<=bench_y+44 and MAP_L+100<=x:
            idx = int((x-MAP_L-100)//72)
            if 0<=idx<len(self.state.bench):
                self.sell(self.state.bench[idx]); return

    def on_key_press(self, key, mod):
        if key == arcade.key.ESCAPE:
            if self.dir_mode:
                self.dir_mode = False; self.dir_op = None; self.selected = None
                self.msg = '取消部署'; self.msg_tmr = 1.0
            elif self.drag_op:
                self.drag_op = None; self.selected = None
                self.msg = '取消拖拽'; self.msg_tmr = 1.0
            else:
                self.selected = None; self.msg = '取消'; self.msg_tmr = 1.0
        elif key == arcade.key.SPACE and self.phase=='battle':
            self.b_speed = 4.0 if self.b_speed<3 else 1.0
            self.msg=f'速度:{self.b_speed}x'; self.msg_tmr=1.0
        elif key == arcade.key.ENTER and self.phase=='rest': self._next_round()
        elif key == arcade.key.R and self.phase=='decision': self.refresh_shop()
        # 方向微调(方向模式中也可用键盘)
        elif key == arcade.key.TAB and self.dir_mode:
            self.deploy_dir = (self.deploy_dir+1)%4
            self.msg = f'方向: {"→↑←↓"[self.deploy_dir]}'; self.msg_tmr=1.0
        elif key == arcade.key.Q and self.dir_mode:
            self.deploy_dir = (self.deploy_dir-1)%4
            self.msg = f'方向: {"→↑←↓"[self.deploy_dir]}'; self.msg_tmr=1.0

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.dir_mode:
            self.deploy_dir = (self.deploy_dir + (1 if scroll_y>0 else -1)) % 4

    def _click_setup(self, x, y):
        diffs = ['入门','标准','险境','绝境','终极']
        lx, ly, rx, ry = int(SW*0.28), SH-200, int(SW*0.72), SH-200
        # ◀▶ 策略切换
        if self.setup_strat_idx > 0 and hit(x, y, lx-140, ly-4, 36, 36):
            self.setup_strat_idx -= 1; return
        if self.setup_strat_idx < len(STRATEGIES)-1 and hit(x, y, lx+140, ly-4, 36, 36):
            self.setup_strat_idx += 1; return
        # 难度横向按钮
        for i in range(5):
            if hit(x, y, rx+(i-2)*80, ry-20, 72, 32):
                self.setup_diff_idx = i; return
        # 开始按钮
        if hit(x, y, SW//2, SH-380, 200, 48):
            self._start_game(); self.phase='decision'
            play_bgm(bgm_rest)

    # ── draw ────────────────────────────────────────
    def on_draw(self):
        self.clear(BG)
        if self.phase == 'setup': self._draw_setup(); return
        if self.phase == 'gameover': self._draw_gameover(); return
        self._draw_map()
        # 战斗中可以跳过静态UI
        self._draw_left()
        self._draw_top()
        if self.phase != 'battle' or not self._grid_drawn:
            self._draw_shop()
        # 过渡遮罩
        if self.transition_alpha > 0:
            a = int(self.transition_alpha * 180)
            arcade.draw_lbwh_rectangle_filled(0, 0, SW, SH, (0,0,0,a))
            if self.transition_msg:
                txt(self.transition_msg, SW//2, SH//2, WHITE, 28)
        if self.msg and self.msg_tmr>0:
            # 消息框: 整备区与地图之间
            st = SH - SHOP_H
            msg_y = (st + (st + 34)) // 2  # st 和 bench_y(st+34) 的中点
            msg_w = min(600, len(self.msg) * 14 + 40)
            draw_panel(SW//2, msg_y, msg_w, 26,
                       (18, 20, 28, 240), GOLD, 1)
            txt(self.msg, SW//2, msg_y - 7, (255, 255, 200), 13)

    def _draw_setup(self):
        # 标题
        txt('卫戍协议', SW//2, SH-75, GOLD, 40, bold=True)
        txt('GARRISON PROTOCOL', SW//2, SH-108, DIM, 14)

        lx, ly = int(SW*0.28), SH-200
        rx, ry = int(SW*0.72), SH-200

        # 左栏: 策略卡片
        txt('策略', lx, ly+45, TEXT, 20)
        s = STRATEGIES[self.setup_strat_idx]
        # 箭头
        if self.setup_strat_idx > 0:
            txt('◀', lx-140, ly+3, WHITE, 24)
        if self.setup_strat_idx < len(STRATEGIES)-1:
            txt('▶', lx+140, ly+3, WHITE, 24)
        draw_card(lx, ly, 260, 60, False, False, GOLD)
        txt(s.name, lx, ly+12, GOLD, 18)
        txt(f'{s.initiator} · HP:{s.hp}', lx, ly-12, DIM, 12)
        eff = s.effect_desc
        for j, ln in enumerate([eff[:28], eff[28:56], eff[56:84]]):
            if ln.strip():
                txt(ln.strip(), lx, ly-30-j*15, CYAN, 10)

        # 右栏: 难度按钮组
        txt('难度', rx, ry+45, TEXT, 20)
        diffs = ["入门","标准","险境","绝境","终极"]
        dcol = [DIM, GREEN, GOLD, ORANGE, RED]
        for i in range(5):
            dbx = rx + (i-2)*80
            sel = i == self.setup_diff_idx
            hov = hit(self.hx, self.hy, dbx, ry-20, 72, 32)
            bg = dcol[i] if sel else BUTTON_BG
            tc = TEXT if sel else DIM
            draw_button(dbx, ry-20, 72, 32, diffs[i], hov, bg, tc, 14,
                        dcol[i] if (sel or hov) else None)

        # 开始按钮
        btn_h = hit(self.hx, self.hy, SW//2, SH-380, 220, 52)
        draw_button(SW//2, SH-380, 220, 52, '开始模拟', btn_h,
                    (35, 95, 40, 240), GREEN, 20, GREEN)

    def _draw_gameover(self):
        won = self.state.life > 0
        rf(SW//2, SH//2, SW, SH, (8, 10, 14, 250))
        color = GREEN if won else RED
        msg = '胜利!' if won else '失败'
        txt(msg, SW//2, SH//2+80, color, 52, bold=True)
        txt(f'剩余生命: {self.state.life}', SW//2, SH//2+30, WHITE, 22)
        txt(f'完成回合: {self.state.round_num}/{self.state.total_waves}', SW//2, SH//2, DIM, 16)
        total_layers = sum(ps.layers for ps in self.state.pact_states.values())
        txt(f'总盟约层数: {total_layers}', SW//2, SH//2-30, GOLD, 18)
        txt(f'难度: {self.state.difficulty} | 策略: {self.state.strategy.name}', SW//2, SH//2-60, DIM, 14)
        txt('点击任意位置退出', SW//2, SH//2-120, DIM, 18)

    def _draw_map(self):
        draw_panel(MAP_L+MAP_W//2, MAP_T+MAP_H//2, MAP_W, MAP_H, (20, 22, 28, 240), DIVIDER)
        # 每帧绘制地图格子
        for x in range(COLS):
            for y in range(ROWS):
                c = self.gmap.get_cell(x,y)
                if not c: continue
                px, py = OX+x*CS, OY+y*CS
                col = {CellType.PATH:C_PATH, CellType.RANGED:C_RANGED, CellType.WALL:C_WALL}.get(c.cell_type, C_WALL)
                rf(px+CS//2, py+CS//2, CS-2, CS-2, col)
                ro(px+CS//2, py+CS//2, CS, CS, (45,45,50))

        # 红门蓝门
        pc = self.gmap.path_cells
        if pc:
            rx, ry = pc[-1]; lx, ly = pc[0]
            rf(OX+rx*CS+CS//2, OY+ry*CS+CS//2, CS-2, CS-2, C_SPAWN)
            txt('入', OX+rx*CS+CS//2, OY+ry*CS+CS//2-8, RED, 15)
            rf(OX+lx*CS+CS//2, OY+ly*CS+CS//2, CS-2, CS-2, C_GOAL)
            txt('守', OX+lx*CS+CS//2, OY+ly*CS+CS//2-8, BLUE, 15)

        # 已部署干员
        ops_source = self.b_ops if self.phase=='battle' else []
        if not ops_source:
            # decision phase: show from state
            for x in range(COLS):
                for y in range(ROWS):
                    c = self.gmap.get_cell(x,y)
                    if c and c.occupied:
                        px, py = OX+x*CS+CS//2, OY+y*CS+CS//2
                        for op in self.state.deployed:
                            if op.uid == c.operator_id:
                                col = GOLD if op.is_elite else (CYAN if op.block_count>0 else PURPLE)
                                arcade.draw_circle_filled(px, py, 22, col)
                                arcade.draw_circle_outline(px, py, 22, (30,30,30), 2)
                                txt(op.name[:3], px, py+25, WHITE, 8)
                                break

        for bo in ops_source:
            px, py = OX+bo['gx']*CS+CS//2, OY+bo['gy']*CS+CS//2
            if not bo['alive']:
                arcade.draw_circle_filled(px, py, 22, (80,80,80))
                arcade.draw_circle_outline(px, py, 22, RED, 3)
                if 'death_timer' in bo:
                    rf(px, py-2, 40, 18, (40,10,10))
                    txt(f'{bo["death_timer"]:.0f}s', px, py-4, RED, 16)
                txt(bo['op'].name[:3], px, py+24, (120,120,120), 9)
                continue
            col = GOLD if bo['op'].is_elite else (CYAN if bo['op'].block_count>0 else PURPLE)
            arcade.draw_circle_filled(px, py, 22, col)
            # 边框: 近战蓝, 奶妈绿, 其余青
            border_c = BLUE if bo['op'].block_count>0 else (GREEN if bo['op'].healer else CYAN)
            arcade.draw_circle_outline(px, py, 22, border_c, 2)
            # HP条(渐变: 绿>黄>红)
            hp_pct = bo['hp']/bo['max_hp']; bw = CS-8
            hp_c = GREEN if hp_pct>0.5 else (YELLOW if hp_pct>0.25 else RED)
            rf(px, py-28, bw, 5, RED)
            rf(px-(bw-int(bw*hp_pct))//2, py-28, int(bw*hp_pct), 5, hp_c)
            txt(bo['op'].name[:4], px, py-18, WHITE, 8)

        # 敌人
        for e in self.enemies:
            if not e['alive']: continue
            col = GOLD if e.get('is_boss') else (RED if e.get('is_elite') else (210,70,60))
            r = 14 if e.get('is_boss') else (11 if e.get('is_elite') else 8)
            arcade.draw_circle_filled(e['x'], e['y'], r, col)
            bw = 2 if e.get('is_boss') else (2 if e.get('is_elite') else 1)
            bcol = GOLD if e.get('is_boss') else (PURPLE if e.get('is_elite') else RED)
            arcade.draw_circle_outline(e['x'], e['y'], r, bcol, bw)
            hp_pct = e['hp']/e['max_hp']; bw=24
            rf(e['x'], e['y']-18, bw, 3, RED)
            rf(e['x']-(bw-int(bw*hp_pct))//2, e['y']-18, int(bw*hp_pct), 3, GREEN)
            # 敌人名字
            txt(e.get('name',''), e['x'], e['y']-22, WHITE, 8)

        # ── 悬停提示(含文本框) ──
        if OX<=self.hx<=OX+COLS*CS and OY<=self.hy<=OY+ROWS*CS:
            hgx, hgy = int((self.hx-OX)//CS), int((self.hy-OY)//CS)
            hcell = self.gmap.get_cell(hgx, hgy)
            if hcell and hcell.occupied:
                for op in (self.state.deployed if self.phase!='battle' else [b['op'] for b in self.b_ops]):
                    if op.uid == hcell.operator_id:
                        pacts = ', '.join(op.pacts)
                        tier = ['I','II','III','IV','V','VI'][min(op.tier-1,5)]
                        # 计算盟约加成
                        atk_m = BattleLogic.calc_atk_mult(self.state, op, self.b_ops)
                        hp_m = BattleLogic.calc_hp_mult(self.state, op, self.b_ops)
                        def_m = BattleLogic.calc_def_mult(self.state, op)
                        _, aspd = BattleLogic.calc_aspd(self.state, op)
                        n_traits = len(op.traits)
                        box_h = 85 + n_traits * 14
                        tx = min(self.hx + 10, SW - 330)
                        ty = max(self.hy - box_h - 10, 10)
                        M = 300; bw = 330
                        draw_panel(tx+bw//2, ty+box_h//2, bw, box_h, (20, 22, 30, 245), GOLD)
                        txt(f'{op.name} [{tier}]', tx+bw//2, ty+box_h-20, WHITE, 15, max_w=M)
                        txt(f'HP:{op.hp}×{hp_m:.1f}={int(op.hp*hp_m)} ATK:{op.atk}×{atk_m:.1f}={int(op.atk*atk_m)}', tx+bw//2, ty+box_h-38, GREEN, 12, max_w=M)
                        txt(f'DEF:{op.defense}×{def_m:.1f}={int(op.defense*def_m)} 攻速+{aspd:.0f}', tx+bw//2, ty+box_h-54, CYAN, 12, max_w=M)
                        txt(f'盟约: {pacts}', tx+bw//2, ty+box_h-70, GOLD, 11, max_w=M)
                        for j, t in enumerate(op.traits):
                            txt(f'特质: {t.description}', tx+bw//2, ty+box_h-86-j*14, DIM, 10, max_w=M)
                        break

        # 伤害数字
        for x,y,t,tt,c in self.dmg_nums:
            txt(t, x, y, c, 11)

        # 攻击线
        for a,b,c,d,tt in self.atk_lines:
            alpha = 200 if tt > 0.1 else 80
            arcade.draw_line(a,b,c,d, (255,200,50,alpha), 2)

        # 地图上方: 敌方波次信息
        if self.phase == 'battle':
            total_enemies = sum(c for _, c in self.waves[self.state.round_num-1].enemies) if self.state.round_num-1 < len(self.waves) else 0
            killed = self.b_killed
            txt(f'敌人: {killed}/{total_enemies}', OX+COLS*CS//2, OY+ROWS*CS+10, RED, 14, font=NUM_FONT)

        # 右下角部署计数
        n = len(self.state.deployed)
        full = n >= self.state.max_operators
        bg = (50, 20, 20, 220) if full else (20, 24, 32, 220)
        draw_panel(OX+COLS*CS-50, OY+ROWS*CS-18, 80, 28, bg, DIVIDER)
        txt(f'{n}/{self.state.max_operators}', OX+COLS*CS-50, OY+ROWS*CS-24, RED if full else WHITE, 14, font=NUM_FONT)

        # ── 部署预览 ──
        # 方向模式: 显示干员+方向箭头+攻击范围
        if self.dir_mode and self.dir_op:
            op = self.dir_op; gx, gy = self.dir_gx, self.dir_gy
            cx, cy = OX+gx*CS+CS//2, OY+gy*CS+CS//2
            # 干员占位圆圈
            col = GOLD if op.is_elite else (CYAN if op.block_count>0 else PURPLE)
            arcade.draw_circle_filled(cx, cy, 22, col)
            arcade.draw_circle_outline(cx, cy, 22, SELECTED_BORDER[:3], 3)
            txt(op.name[:4], cx, cy+28, WHITE, 10)
            # 方向箭头
            dirs = [(1,0,'→'), (0,1,'↑'), (-1,0,'←'), (0,-1,'↓')]
            for i, (dx, dy, arrow) in enumerate(dirs):
                ax = cx + dx*CS; ay = cy + dy*CS
                ac = GOLD if i == self.deploy_dir else DIM
                asize = 18 if i == self.deploy_dir else 12
                txt(arrow, ax, ay, ac, asize)
            # 攻击范围预览(当前方向)
            for rx, ry in self._calc_range(gx, gy, op):
                rpx, rpy = OX+rx*CS, OY+ry*CS
                rf(rpx+CS//2, rpy+CS//2, CS-3, CS-3, (255, 180, 60, 80))
            # 半透明提示
            txt('拖拽方向 · 点击确认', cx, cy-32, GOLD, 10)
        # 拖拽中: 显示干员在鼠标位置
        elif self.drag_op and OX<=self.hx<=OX+COLS*CS and OY<=self.hy<=OY+ROWS*CS:
            gx, gy = int((self.hx-OX)//CS), int((self.hy-OY)//CS)
            px, py = OX+gx*CS+CS//2, OY+gy*CS+CS//2
            cell = self.gmap.get_cell(gx, gy)
            valid = cell and not cell.occupied and self.gmap.can_deploy(gx, gy, self.drag_op.block_count>0)
            bc = GREEN if valid else RED
            ro(px, py, CS-2, CS-2, bc, 2)
            txt(self.drag_op.name[:4], px, py-2, WHITE, 10)
        # 无拖拽时: 点击地图查看已部署干员信息(保持在battle模式下)
        # (不再需要旧的selected+click部署逻辑)

    def _draw_left(self):
        draw_panel(LEFT_W//2, MAP_T+MAP_H//2, LEFT_W, MAP_H, (22, 25, 32, 240), DIVIDER)
        # 退出按钮
        exit_hover = hit(self.hx, self.hy, 27, MAP_T+26, 44, 36)
        draw_button(27, MAP_T+26, 44, 36, '退出', exit_hover, (55, 20, 20, 230), RED, 12, RED)

    def _draw_top(self):
        # 半透明浮层背景
        draw_panel(SW//2, TOP_H//2, SW, TOP_H, (22, 25, 32, 230), DIVIDER)
        if not self.state: return

        phases = {'decision':'整备中','battle':'战斗中','rest':'休整期','gameover':'结束'}
        # 左侧信息组 - 按文本实际宽度动态计算间距
        info_parts = [
            (f'回合 {self.state.round_num}/{self.state.total_waves}', TEXT, 15),
            (phases.get(self.phase, '?'), GOLD, 15),
            (f'HP {self.state.life}', RED if self.state.life<10 else GREEN, 15),
            (f'Lv.{self.center_lv} | {self.state.difficulty}', DIM, 12),
        ]
        ix = MAP_L + 16
        for label, col, sz in info_parts:
            txt(label, ix, TOP_H//2, col, sz, 'left')
            ix += len(label) * (sz + 2) + 24

        # 盟约徽章(右侧, 紧凑排列)
        ax = SW - 16
        active_list = sorted([p for p in self.state.pact_states.values() if p.active], key=lambda x: -x.layers)
        visible = active_list[:8]
        overflow = len(active_list) - 8
        for ps in visible:
            is_core = ps.pact.is_core
            bg_c = (50, 25, 70, 230) if is_core else (25, 45, 35, 230)
            border_c = PURPLE if is_core else GREEN
            bx_cx = ax - 38
            rf(bx_cx, TOP_H//2, 70, 22, bg_c)
            ro(bx_cx, TOP_H//2, 70, 22, border_c)
            txt(f'{ps.pact.name} Lv.{ps.layers}', bx_cx, TOP_H//2 - 7, WHITE, 8)
            ax -= 78
            # 悬停详情
            if self.hy < TOP_H and bx_cx-35 < self.hx < bx_cx+35 and self.hy < TOP_H:
                info = ps.pact.effect_desc[:60]
                adv = (ps.pact.advanced_desc or '')[:60]
                tx = min(self.hx + 10, SW - 320); ty = TOP_H + 5
                pact_ops_list = PACT_OPS.get(ps.pact.id, [])
                owned_ids = {o.id: o.name for o in self.state.roster}
                lines = 3 + (1 if adv else 0) + (len(pact_ops_list) + 3) // 4
                bh = 20 * lines + 24
                draw_panel(tx+150, ty+bh//2, 300, bh, (25, 28, 40, 240), GOLD)
                txt(f'【{ps.pact.name}】{ps.layers}层 在场{ps.operator_count}人', tx+150, ty+bh-18, GOLD, 13, max_w=280)
                txt(info, tx+150, ty+bh-36, TEXT, 10, max_w=280)
                if adv: txt(adv, tx+150, ty+bh-52, CYAN, 10, max_w=280)
                y2 = ty + bh - 68
                for j, name in enumerate(pact_ops_list[:12]):
                    c = GREEN if name in owned_ids.values() else DIM
                    nx = tx + 20 + (j % 4) * 70
                    ny = y2 - (j // 4) * 14
                    txt(name, nx, ny, c, 9, 'left')
            if ax < MAP_L + 550: break
        if overflow > 0:
            txt(f'+{overflow}', ax + 90, TOP_H//2, DIM, 10, 'right')

    def _draw_shop(self):
        st = SH - SHOP_H
        draw_panel(SW//2, st + SHOP_H//2, SW, SHOP_H, PANEL_BG, DIVIDER)

        # ═══ 底部按钮行 (st+2 ~ st+32) ═══
        by = st + 16
        # 升级中心 - 紧贴左侧面板
        uc_hov = hit(self.hx, self.hy, MAP_L+65, by, 72, 28)
        can_up = self.center_lv < 6
        uc_bg = HOVER_BRIGHT if (uc_hov and can_up) else BUTTON_BG
        draw_button(MAP_L+65, by, 72, 28,
                    f'升级 ${self.center_upgrade_cost}',
                    uc_hov and can_up, uc_bg,
                    GREEN if can_up else DIM, 10)
        # 冻结 + 刷新 + 资金 - 全部靠右, 逐项左移
        # 右边距: 从 SW 边缘往左排
        rx = SW - 20  # 右边缘留20px
        # 资金
        funds = f'${self.state.funds}'
        est_funds_w = len(funds) * 14  # 字号22, CJK近似
        txt(funds, rx - est_funds_w//2, by - 6, GOLD, 22, font=NUM_FONT)
        rx -= est_funds_w + 10
        # 刷新
        fr = getattr(self.state, 'free_refreshes', 0)
        ref_label = f'免费x{fr}' if fr > 0 else '刷新 $2'
        ref_col = GREEN if fr > 0 else GOLD
        ref_hov = hit(self.hx, self.hy, rx-35, by, 70, 28)
        draw_button(rx-35, by, 70, 28, ref_label, ref_hov, BUTTON_BG, ref_col, 11)
        rx -= 78
        # 冻结
        freeze_hov = hit(self.hx, self.hy, rx-35, by, 70, 28)
        draw_button(rx-35, by, 70, 28,
                    '解冻' if self.frozen else '冻结', freeze_hov,
                    (60, 40, 20, 230) if self.frozen else BUTTON_BG, CYAN, 11)

        # ═══ 整备区 (st+34 ~ st+78, 高度44) ═══
        bench_y = st + 34
        txt(f'整备区({len(self.state.bench)})', MAP_L+8, bench_y+40, DIM, 10, 'left')
        for i, op in enumerate(self.state.bench[:14]):
            bx = MAP_L + 100 + i * 72
            sel = self.selected and op.uid == self.selected.uid
            hov = hit(self.hx, self.hy, bx+46, bench_y+22, 66, 44)
            draw_card(bx+46, bench_y+22, 66, 44, hov, sel, tier_color(op.tier))
            txt(op.name[:4], bx+46, bench_y+35, WHITE, 10, max_w=60)
            et = '[E]' if op.is_elite else ''
            txt(f'{et}[{tier_badge(op.tier)}]', bx+46, bench_y+24, GOLD, 8)
            txt(f'${op.cost}', bx+46, bench_y+12, GOLD, 10, font=NUM_FONT)
            pnames = '/'.join(PACT_NAMES.get(p, p) for p in op.pacts[:2])
            txt(pnames, bx+46, bench_y+2, CYAN, 7)
            if hov:
                n = len(op.traits)
                bh = 30 + n * 16
                ty2 = max(bench_y + 50 - bh, 10)
                draw_panel(bx+46, ty2+bh//2, 280, bh, (25, 28, 40, 245), GOLD)
                txt(f'{op.name} 特质', bx+46, ty2+bh-18, CYAN, 12, max_w=260)
                for j, t in enumerate(op.traits):
                    txt(t.description, bx+46, ty2+bh-34-j*16, DIM, 11, max_w=260)

        # ═══ 商店 (st+80 ~ st+128, 高度48) ═══
        sy = st + 80
        txt('商店', MAP_L+8, sy+38, GOLD, 10, 'left')
        for i in range(5):
            bx = MAP_L + 100 + i * 140
            card_cx = bx + 65
            if i < len(self.shop_ops) and not self.shop_owned[i]:
                op = self.shop_ops[i]; t = op.tier
                hov = hit(self.hx, self.hy, card_cx, sy+24, 122, 48)
                draw_card(card_cx, sy+24, 122, 48, hov, False, tier_color(t))
                txt(f'{op.name}[{tier_badge(t)}]', card_cx, sy+34, WHITE, 11, max_w=112)
                if op.is_elite:
                    rf(card_cx+54, sy+38, 16, 10, RED)
                    txt('E', card_cx+54, sy+34, WHITE, 7)
                pnames = '/'.join(PACT_NAMES.get(p, p) for p in op.pacts[:2])
                txt(pnames, card_cx, sy+22, CYAN, 8, max_w=112)
                txt(f'${op.cost}', card_cx, sy+8, GOLD, 13, font=NUM_FONT)
                if hov:
                    n = len(op.traits)
                    bh = 30 + n * 16
                    ty2 = max(sy - 40 - bh, 10)
                    draw_panel(card_cx, ty2+bh//2, 280, bh, (25, 28, 40, 245), GOLD)
                    txt(f'{op.name} 特质', card_cx, ty2+bh-18, CYAN, 12, max_w=260)
                    for j, t in enumerate(op.traits):
                        txt(t.description, card_cx, ty2+bh-34-j*16, DIM, 11, max_w=260)
            else:
                owned = i < len(self.shop_ops) and self.shop_owned[i]
                draw_panel(card_cx, sy+24, 126, 48, (28, 30, 36, 200), DIVIDER)
                if owned:
                    txt('已购', card_cx, sy+24, DIM, 13)

        # 晋升奖励
        if self.promo_ops:
            py2 = st - 20
            draw_panel(MAP_L+100+200, py2+14, 600, 40, (35, 25, 15, 240), GOLD)
            txt('晋升奖励! 点击获取(免费)', MAP_L+100+200, py2+20, GOLD, 11)
            for i, op in enumerate(self.promo_ops):
                bx = MAP_L + 100 + i * 140
                hov = hit(self.hx, self.hy, bx+65, py2-30, 126, 52)
                draw_card(bx+65, py2-30, 126, 52, hov, False, GOLD)
                txt(f'{op.name} [{tier_badge(op.tier)}]', bx+65, py2-20, WHITE, 11, max_w=110)
                txt('免费!', bx+65, py2-34, GREEN, 10)
                pnames = '/'.join(PACT_NAMES.get(p, p) for p in op.pacts[:2])
                txt(pnames, bx+65, py2-44, CYAN, 9)

        # 战斗/倍速
        if self.phase == 'decision':
            bh = hit(self.hx, self.hy, SW-70, st+SHOP_H-20, 100, 32)
            draw_button(SW-70, st+SHOP_H-20, 100, 32, '开始战斗', bh,
                        (35, 95, 35, 240), GREEN, 14, GREEN)
        if self.phase == 'battle':
            txt(f'DP: {self.b_dp}', MAP_L+240, by-6, BLUE, 20, 'left', font=NUM_FONT)
            for i, sp in enumerate([1, 2, 5, 8]):
                bx = MAP_L + 320 + i * 75
                active = self.b_speed == sp
                h = hit(self.hx, self.hy, bx, by, 68, 32)
                draw_button(bx, by, 68, 32, f'{sp}x',
                            h, HOVER_BRIGHT if active else BUTTON_BG,
                            WHITE if active else DIM, 16,
                            GOLD if active else None)


def run_arcade(difficulty='标准', strategy_id='s1'):
    game = GarrisonWindow()
    game.setup_strat_idx = next((i for i,s in enumerate(STRATEGIES) if s.id==strategy_id), 0)
    game.setup_diff_idx = {'入门':0,'标准':1,'险境':2,'绝境':3,'终极':4}.get(difficulty, 1)
    # 显示设置界面, 不直接开始
    game.phase = 'setup'
    arcade.run()
    return game.state
