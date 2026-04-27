"""
engine.py — منصة الحبي للتداول
استراتيجية الحبي (Habbi Strategy) — Price Action Only, No Time Filters

المراحل:
  1. Daily Sweep Detection — كسر قاع/قمة يومية + تصنيف نوع السيولة
  2. SMT Divergence — تأكيد بين الأصل والـ SMT
  3. MSS on H1 — كسر البنية بعد السحب (بدون فلتر وقت)
  4. IFVG + 50% EQ Entry — الدخول عند نصف منطقة الـ IFVG
  5. External Liquidity Targets — الأهداف البعيدة (الموجة الكاملة)
  6. Confidence Gate — بوابة القرار الشاملة
"""

import warnings; warnings.filterwarnings("ignore")

import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, field
from typing import Optional, List

# ═══════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════
HTF_INTERVAL   = "1d"
H4_INTERVAL    = "4h"
H1_INTERVAL    = "1h"
M15_INTERVAL   = "15m"
HTF_PERIOD     = "6mo"
H4_PERIOD      = "60d"
H1_PERIOD      = "30d"
M15_PERIOD     = "10d"

SWING_LB          = 5
HTF_CANDLES       = 100
LIQUIDITY_TOUCHES = 2
SMT_WINDOW        = 20
SMT_TOLERANCE     = 0.003
DAILY_SWEEP_TOL   = 0.001
IFVG_LOOKBACK     = 15
EXT_LIQ_LOOKBACK  = 60
MIN_RR            = 2.0
SWEEP_WICK_MIN    = 8.0
SCORE_A_PLUS = 10
SCORE_A      = 7
SCORE_MIN    = 4

# ─── Watchlists ─────────────────────────────────────────────
TECH_STOCKS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","AMD","QCOM",
    "ORCL","CRM","ADBE","INTC","TXN","MU","AMAT","LRCX","KLAC","MRVL",
    "NFLX","PYPL","SHOP","SNOW","PANW","CRWD","ZS","DDOG","MSTR","PLTR",
]
BLUE_CHIPS = [
    "JPM","BAC","GS","MS","BRK-B","V","MA","AXP","WFC","C",
    "JNJ","UNH","LLY","ABBV","PFE","MRK","TMO","ABT","DHR","BMY",
    "WMT","HD","COST","TGT","MCD","SBUX","NKE","LOW","TJX","AMGN",
    "XOM","CVX","COP","SLB","CAT","RTX","HON","UPS","BA","GE",
]
CHEAP_STOCKS = [
    "F","AAL","SOFI","RIVN","LCID","SNAP","UBER","LYFT","PLUG","NIO",
    "XPEV","CLNE","NOK","BB","SIRI","VALE","ITUB","PBR","KGC","BTG",
]
CRYPTO_ETF = [
    "MSTR","COIN","BITO","GBTC","ETHE","ARKK","BLOK","BTCW","HODL","EZBC",
]
WATCHLIST_PRESETS = {
    "Options (70 Stocks)": [(t,"QQQ") for t in TECH_STOCKS]+[(t,"SPY") for t in BLUE_CHIPS],
    "Tech Mega-Cap (30)":  [(t,"QQQ") for t in TECH_STOCKS],
    "Blue Chips S&P (40)": [(t,"SPY") for t in BLUE_CHIPS],
    "Cheap Stocks (<$20)": [(t,"SPY") for t in CHEAP_STOCKS],
    "Crypto ETFs":         [(t,"QQQ") for t in CRYPTO_ETF],
}

# ═══════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════
@dataclass
class LiquidityLevel:
    price: float
    kind: str
    touches: int
    formed_at: pd.Timestamp
    timeframe: str
    is_dol: bool = False

@dataclass
class SMTSignal:
    direction: str
    asset1_swing: float
    asset2_swing: float
    detected_at: pd.Timestamp
    description: str
    score: int = 2

@dataclass
class SwingPoint:
    index: int
    timestamp: pd.Timestamp
    price: float
    kind: str

@dataclass
class LiqSweep:
    direction: str
    swept_price: float
    swept_at: pd.Timestamp
    swept_idx: int
    close_after: float
    wick_pct: float
    sweep_tf: str = "Daily"
    strength: str = field(init=False)
    def __post_init__(self):
        if self.wick_pct > 40:   self.strength = "STRONG"
        elif self.wick_pct > 25: self.strength = "MEDIUM"
        else:                    self.strength = "WEAK"

@dataclass
class StructureBreak:
    kind: str
    direction: str
    break_price: float
    broke_at: pd.Timestamp
    candle_idx: int

@dataclass
class IFVG:
    direction: str
    top: float
    bottom: float
    midpoint: float
    formed_at: pd.Timestamp
    candle_idx: int
    size_pct: float
    filled: bool = False
    inverted: bool = False

@dataclass
class ExternalLiquidity:
    price: float
    kind: str
    formed_at: pd.Timestamp
    timeframe: str
    distance_pct: float
    rr_ratio: float = 0.0

@dataclass
class Target:
    label: str
    price: float
    rr: float
    kind: str
    is_tp: bool = True
    level: float = 0.0

@dataclass
class DecisionLog:
    stage: str
    finding: str
    score_delta: int
    reasoning: str
    risk_note: str = ""

@dataclass
class TradeSetup:
    ticker: str
    bias: str
    entry: float
    stop_loss: float
    targets: List[Target]
    pd_array: None
    score: int
    grade: str
    decision_log: List[DecisionLog]
    dol: Optional[LiquidityLevel]
    smt: Optional[SMTSignal]
    sweep: Optional[LiqSweep]
    mss: Optional[StructureBreak]
    fvg_entry: Optional[IFVG]
    ext_liq: Optional[ExternalLiquidity]
    time_ctx: None = None
    risk_summary: str = ""
    liquidity_type: str = "Daily"
    wave_target: float = 0.0
    ifvg_eq_50: float = 0.0

# ═══════════════════════════════════════════════════════════
#  TZ HELPERS
# ═══════════════════════════════════════════════════════════
def to_naive(ts):
    if ts is None: return None
    try:
        t = pd.Timestamp(ts)
        return t.tz_localize(None) if t.tzinfo is not None else t
    except Exception: return None

def naive_index(idx):
    try:
        if hasattr(idx,"tz") and idx.tz is not None: return idx.tz_localize(None)
        return idx
    except Exception:
        try: return idx.tz_convert(None)
        except Exception: return idx

# ═══════════════════════════════════════════════════════════
#  DATA LAYER
# ═══════════════════════════════════════════════════════════
def fetch(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval,
                     auto_adjust=True, progress=False)
    if df.empty: raise ValueError(f"No data: {ticker}")
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
    return df[["Open","High","Low","Close","Volume"]].dropna()

def detect_swings(df, lookback=5, n=100):
    sl = df.iloc[-n:].copy().reset_index()
    swings = []
    def _ts(i):
        for c in ["Datetime","Date"]:
            if c in sl.columns: return pd.Timestamp(sl[c].iloc[i])
        return sl.index[i]
    for i in range(lookback, len(sl)-lookback):
        wh = sl["High"].iloc[i-lookback:i+lookback+1]
        wl = sl["Low"].iloc[i-lookback:i+lookback+1]
        if sl["High"].iloc[i] == wh.max():
            swings.append(SwingPoint(i, _ts(i), float(sl["High"].iloc[i]), "high"))
        if sl["Low"].iloc[i] == wl.min():
            swings.append(SwingPoint(i, _ts(i), float(sl["Low"].iloc[i]), "low"))
    return _dedup(swings, lookback)

def _dedup(swings, w):
    def keep(pts, mode):
        if not pts: return []
        res, grp = [], [pts[0]]
        for p in pts[1:]:
            if abs(p.index - grp[-1].index) <= w: grp.append(p)
            else:
                res.append(max(grp,key=lambda x:x.price) if mode=="high" else min(grp,key=lambda x:x.price))
                grp = [p]
        res.append(max(grp,key=lambda x:x.price) if mode=="high" else min(grp,key=lambda x:x.price))
        return res
    h = keep([s for s in swings if s.kind=="high"],"high")
    l = keep([s for s in swings if s.kind=="low"],"low")
    return sorted(h+l, key=lambda x:x.index)

# ═══════════════════════════════════════════════════════════
#  STAGE 1 — Daily Sweep + Liquidity Classification
# ═══════════════════════════════════════════════════════════
def stage1_daily_sweep(df_daily, df_h1, df_h4=None):
    current = float(df_daily["Close"].iloc[-1])
    swings_d = detect_swings(df_daily, SWING_LB, HTF_CANDLES)
    liq_lvls = _build_liq(df_daily, swings_d, "Daily")
    if df_h4 is not None and not df_h4.empty:
        swings_h4 = detect_swings(df_h4, SWING_LB, 80)
        liq_lvls += _build_liq(df_h4, swings_h4, "4H")

    bsl = sorted([l for l in liq_lvls if l.kind=="BSL" and l.price>current], key=lambda x:(-x.touches,x.price))
    ssl = sorted([l for l in liq_lvls if l.kind=="SSL" and l.price<current], key=lambda x:(-x.touches,-x.price))
    htf_mid = (float(df_daily["High"].iloc[-50:].max()) + float(df_daily["Low"].iloc[-50:].min())) / 2
    htf_bias = "bearish" if current > htf_mid else "bullish"

    dol = None
    if htf_bias=="bearish" and ssl:   dol = ssl[0]
    elif htf_bias=="bullish" and bsl: dol = bsl[0]
    elif bsl: dol = bsl[0]
    elif ssl: dol = ssl[0]
    if dol: dol.is_dol = True

    bias = ("long" if dol and dol.price>current else
            "short" if dol and dol.price<current else
            "long" if htf_bias=="bullish" else "short")

    sweep, liq_type = _find_sweep(df_daily, df_h1, df_h4, bias)
    return sweep, liq_lvls, dol, bias, liq_type

def _build_liq(df, swings, tf):
    levels = []
    for h in [s for s in swings if s.kind=="high"]:
        t = _touches(h.price, df, "high")
        if t >= LIQUIDITY_TOUCHES: levels.append(LiquidityLevel(h.price,"BSL",t,h.timestamp,tf))
    for l in [s for s in swings if s.kind=="low"]:
        t = _touches(l.price, df, "low")
        if t >= LIQUIDITY_TOUCHES: levels.append(LiquidityLevel(l.price,"SSL",t,l.timestamp,tf))
    if not levels:
        for h in [s for s in swings if s.kind=="high"][-3:]:
            levels.append(LiquidityLevel(h.price,"BSL",1,h.timestamp,tf))
        for l in [s for s in swings if s.kind=="low"][-3:]:
            levels.append(LiquidityLevel(l.price,"SSL",1,l.timestamp,tf))
    return levels

def _touches(price, df, side, tol=0.002):
    count = 0
    for i in range(len(df)):
        ref = float(df["High"].iloc[i]) if side=="high" else float(df["Low"].iloc[i])
        if abs(ref-price)/max(price,0.0001) <= tol: count += 1
    return count

def _find_sweep(df_daily, df_h1, df_h4, bias):
    if len(df_daily) < 2: return None, "غير محدد"
    ph = float(df_daily["High"].iloc[-2])
    pl = float(df_daily["Low"].iloc[-2])

    sw = _sweep_in(df_h1, ph, pl, bias, "Daily")
    if sw: return sw, "يومي · Daily"

    if df_h4 is not None and len(df_h4) >= 3:
        h4h = float(df_h4["High"].iloc[-3])
        h4l = float(df_h4["Low"].iloc[-3])
        sw4 = _sweep_in(df_h1, h4h, h4l, bias, "4H")
        if sw4: return sw4, "4 ساعات · 4H"

    sw1h = _sweep_h1_internal(df_h1, bias)
    if sw1h: return sw1h, "ساعة · 1H"

    return None, "غير محدد"

def _sweep_in(df, ref_high, ref_low, bias, tf_label):
    win = df.iloc[-60:].copy().reset_index()
    if win.empty: return None
    def _ts(row):
        for c in ["Datetime","Date"]:
            if c in row.index: return pd.Timestamp(row[c])
        return pd.Timestamp.now()
    for i in range(1, len(win)):
        row = win.iloc[i]
        ch,cl,co,cc = float(row["High"]),float(row["Low"]),float(row["Open"]),float(row["Close"])
        rng = max(ch-cl, 0.0001)
        if bias=="long" and cl < ref_low*(1-DAILY_SWEEP_TOL) and cc > ref_low:
            return LiqSweep("sellside",ref_low,_ts(row),i,cc,max((min(co,cc)-cl)/rng*100,5.0),tf_label)
        if bias=="short" and ch > ref_high*(1+DAILY_SWEEP_TOL) and cc < ref_high:
            return LiqSweep("buyside",ref_high,_ts(row),i,cc,max((ch-max(co,cc))/rng*100,5.0),tf_label)
    return None

def _sweep_h1_internal(df_h1, bias):
    sw_h1 = detect_swings(df_h1, SWING_LB, 60)
    highs = sorted([s for s in sw_h1 if s.kind=="high"],key=lambda x:-x.price)
    lows  = sorted([s for s in sw_h1 if s.kind=="low"], key=lambda x:x.price)
    if highs and lows:
        return _sweep_in(df_h1, highs[0].price, lows[0].price, bias, "1H")
    return None

# ═══════════════════════════════════════════════════════════
#  STAGE 2 — SMT Divergence
# ═══════════════════════════════════════════════════════════
def stage2_smt_divergence(df1, df2, bias, window=None, tol=None):
    if window is None: window = SMT_WINDOW
    if tol is None:    tol    = SMT_TOLERANCE
    common = df1.index.intersection(df2.index)
    if len(common) < window*2: return None, "insufficient_data"
    a1 = df1.loc[common].iloc[-window:]
    a2 = df2.loc[common].iloc[-window:]
    half = window//2
    a1_ph = float(a1.iloc[:half]["High"].max()); a2_ph = float(a2.iloc[:half]["High"].max())
    a1_ch = float(a1.iloc[half:]["High"].max()); a2_ch = float(a2.iloc[half:]["High"].max())
    a1_pl = float(a1.iloc[:half]["Low"].min());  a2_pl = float(a2.iloc[:half]["Low"].min())
    a1_cl = float(a1.iloc[half:]["Low"].min());  a2_cl = float(a2.iloc[half:]["Low"].min())
    det = a1.index[-1]
    if a1_ch > a1_ph*(1+tol) and a2_ch < a2_ph*(1-tol):
        pct = abs(a1_ch/a1_ph - a2_ch/a2_ph)*100
        return SMTSignal("bearish",a1_ch,a2_ch,det,f"Higher High vs Lower High | {pct:.2f}%"), "bearish_divergence"
    if a1_cl < a1_pl*(1-tol) and a2_cl > a2_pl*(1+tol):
        pct = abs(a1_cl/a1_pl - a2_cl/a2_pl)*100
        return SMTSignal("bullish",a1_cl,a2_cl,det,f"Lower Low vs Higher Low | {pct:.2f}%"), "bullish_divergence"
    if (a1_ch>a1_ph and a2_ch>a2_ph) or (a1_cl<a1_pl and a2_cl<a2_pl):
        return None, "aligned_move"
    return None, "no_divergence"

# ═══════════════════════════════════════════════════════════
#  STAGE 3 — MSS on H1 (No Time Filter)
# ═══════════════════════════════════════════════════════════
def stage3_mss_confirmation(df_h1, sweep, bias):
    if sweep is None: return None
    win = df_h1.iloc[-60:]
    if win.empty: return None
    if bias == "long":
        ref = float(win["High"].iloc[:-5].max()) if len(win)>10 else float(win["High"].max())
        for i in range(5, len(win)):
            if float(win["Close"].iloc[i]) > ref:
                return StructureBreak("MSS","bullish",ref,win.index[i],i)
        recent = float(win["High"].iloc[-15:-1].max()) if len(win)>15 else ref
        for i in range(3, len(win)):
            if float(win["Close"].iloc[i]) > recent*0.998:
                return StructureBreak("BOS","bullish",recent,win.index[i],i)
    else:
        ref = float(win["Low"].iloc[:-5].min()) if len(win)>10 else float(win["Low"].min())
        for i in range(5, len(win)):
            if float(win["Close"].iloc[i]) < ref:
                return StructureBreak("MSS","bearish",ref,win.index[i],i)
        recent = float(win["Low"].iloc[-15:-1].min()) if len(win)>15 else ref
        for i in range(3, len(win)):
            if float(win["Close"].iloc[i]) < recent*1.002:
                return StructureBreak("BOS","bearish",recent,win.index[i],i)
    return None

# ═══════════════════════════════════════════════════════════
#  STAGE 4 — IFVG + 50% EQ Entry
# ═══════════════════════════════════════════════════════════
def stage4_ifvg_entry(df_h1, df_m15, mss, bias):
    if mss is None: return None, None
    ifvg = _find_ifvg(df_m15, mss, bias) or _find_ifvg(df_h1, mss, bias)
    if ifvg:
        ifvg.inverted = True
        return ifvg, ifvg.midpoint
    eq50 = _leg_eq(df_h1, bias)
    if eq50:
        buf = eq50*0.003
        dummy = IFVG(mss.direction,eq50+buf,eq50-buf,eq50,mss.broke_at,mss.candle_idx,0.3)
        return dummy, eq50
    return None, None

def _find_ifvg(df, mss, bias):
    win = df.iloc[-40:]
    if len(win) < 3: return None
    cands = []
    for i in range(2, len(win)):
        c1,c3 = win.iloc[i-2],win.iloc[i]
        if bias=="long" and mss.direction=="bullish":
            gb,gt = float(c1["High"]),float(c3["Low"])
            if gt>gb:
                sz=(gt-gb)/gb*100
                if sz>0.05: cands.append(IFVG("bullish",gt,gb,(gt+gb)/2,win.index[i],i,round(sz,3)))
        elif bias=="short" and mss.direction=="bearish":
            gt,gb = float(c1["Low"]),float(c3["High"])
            if gt>gb:
                sz=(gt-gb)/gt*100
                if sz>0.05: cands.append(IFVG("bearish",gt,gb,(gt+gb)/2,win.index[i],i,round(sz,3)))
    return max(cands,key=lambda x:x.size_pct) if cands else None

def _leg_eq(df, bias):
    win = df.iloc[-30:]
    if win.empty: return None
    return (float(win["High"].max()) + float(win["Low"].min())) / 2

# ═══════════════════════════════════════════════════════════
#  STAGE 5 — External Liquidity (Full Wave Targets)
# ═══════════════════════════════════════════════════════════
def stage5_external_liquidity(df_daily, df_h1, bias, entry, sl):
    current  = float(df_daily["Close"].iloc[-1])
    sl_dist  = max(abs(entry-sl), abs(current*0.005))
    targets  = []
    sw_d     = detect_swings(df_daily, SWING_LB, EXT_LIQ_LOOKBACK)
    sw_h1    = detect_swings(df_h1,    SWING_LB, 80)

    if bias == "long":
        h1_highs = sorted([s for s in sw_h1 if s.kind=="high" and s.price>current], key=lambda x:x.price)
        for i,sw in enumerate(h1_highs[:2]):
            rr = abs(sw.price-entry)/sl_dist
            targets.append(Target(f"TP{i+1} H1 BSL",round(sw.price,4),round(rr,2),f"tp{i+1}",True,float(i+1)))
        d_highs = sorted([s for s in sw_d if s.kind=="high" and s.price>current], key=lambda x:x.price)
        if d_highs:
            eh=d_highs[0]; rr=abs(eh.price-entry)/sl_dist
            if rr>=MIN_RR:
                targets.append(Target("🎯 موجة كاملة Daily BSL",round(eh.price,4),round(rr,2),"ext_liq",True,3.0))
        if len(d_highs)>1:
            eh2=d_highs[1]; rr2=abs(eh2.price-entry)/sl_dist
            if rr2>=MIN_RR*1.5:
                targets.append(Target("🚀 هدف ممتد Extended BSL",round(eh2.price,4),round(rr2,2),"ext_liq",True,4.0))
    else:
        h1_lows = sorted([s for s in sw_h1 if s.kind=="low" and s.price<current], key=lambda x:-x.price)
        for i,sw in enumerate(h1_lows[:2]):
            rr = abs(entry-sw.price)/sl_dist
            targets.append(Target(f"TP{i+1} H1 SSL",round(sw.price,4),round(rr,2),f"tp{i+1}",True,float(i+1)))
        d_lows = sorted([s for s in sw_d if s.kind=="low" and s.price<current], key=lambda x:-x.price)
        if d_lows:
            el=d_lows[0]; rr=abs(entry-el.price)/sl_dist
            if rr>=MIN_RR:
                targets.append(Target("🎯 موجة كاملة Daily SSL",round(el.price,4),round(rr,2),"ext_liq",True,3.0))
        if len(d_lows)>1:
            el2=d_lows[1]; rr2=abs(entry-el2.price)/sl_dist
            if rr2>=MIN_RR*1.5:
                targets.append(Target("🚀 هدف ممتد Extended SSL",round(el2.price,4),round(rr2,2),"ext_liq",True,4.0))

    ext_ts = [t for t in targets if t.kind=="ext_liq"]
    ext_liq = None
    if ext_ts:
        best = max(ext_ts, key=lambda x:x.rr)
        ext_liq = ExternalLiquidity(
            best.price, "ext_high" if bias=="long" else "ext_low",
            df_daily.index[-1], "Daily",
            abs(best.price-current)/current*100, best.rr)
    wave_tgt = 0.0
    if ext_ts:
        wave_tgt = max(t.price for t in ext_ts) if bias=="long" else min(t.price for t in ext_ts)
    return targets, ext_liq, wave_tgt

# ═══════════════════════════════════════════════════════════
#  STAGE 6 — Confidence Gate
# ═══════════════════════════════════════════════════════════
def stage6_confidence_gate(sweep,mss,ifvg,eq50,smt,smt_status,
                            liq_levels,dol,targets,ext_liq,
                            df_h1,bias,ticker,liquidity_type):
    logs=[]; total=0
    current=float(df_h1["Close"].iloc[-1])

    if sweep:
        sc={"Daily":4,"4H":3,"1H":2,"Weekly":5}.get(sweep.sweep_tf.split(" ")[0],2)
        total+=sc
        logs.append(DecisionLog("المرحلة 1 — سحب السيولة",
            f"{sweep.sweep_tf} @ {sweep.swept_price:.4f} ({sweep.strength})",sc,
            f"كُسر المستوى وأُغلق في الاتجاه المعاكس. نوع السيولة: {liquidity_type}",
            "تأكد من أن السعر لا يعود لكسر مستوى الـ SL."))
    else:
        logs.append(DecisionLog("المرحلة 1 — سحب السيولة","❌ لا يوجد سحب مكتمل",0,
            "الشرط الأساسي غير محقق.","انتظر سحباً واضحاً."))

    if mss:
        sc=3 if mss.kind=="MSS" else 2; total+=sc
        logs.append(DecisionLog("المرحلة 2 — كسر البنية H1",
            f"{mss.kind} {mss.direction.upper()} @ {mss.break_price:.4f}",sc,
            f"تأكيد بنيوي: {'صعودي' if mss.direction=='bullish' else 'هبوطي'}.",
            "BOS أضعف من MSS."))
    else:
        logs.append(DecisionLog("المرحلة 2 — كسر البنية H1","⚠️ لا MSS/BOS بعد",0,
            "انتظر كسر البنية قبل الدخول.",""))

    if smt:
        sc=2 if ((smt.direction=="bullish" and bias=="long") or
                 (smt.direction=="bearish" and bias=="short")) else 0
        total+=sc
        logs.append(DecisionLog("المرحلة 3 — SMT",
            f"{'⚡ تأكيد' if sc else '⚠️ تعارض'} · {smt.description[:60]}",sc,
            "الانحراف يؤكد التلاعب.",
            "" if sc else "SMT يعارض التحيز."))
    else:
        sc=1 if smt_status=="aligned_move" else 0; total+=sc
        logs.append(DecisionLog("المرحلة 3 — SMT",
            "✓ تحرك متوافق" if sc else "○ لا انحراف",sc,"",""))

    if ifvg and eq50:
        sc=3 if ifvg.inverted else 2; total+=sc
        logs.append(DecisionLog("المرحلة 4 — IFVG · 50% EQ",
            f"{'IFVG' if ifvg.inverted else 'EQ'} @ {eq50:.4f}",sc,
            f"نقطة الدخول عند 50% EQ = {eq50:.4f}.",""))
    else:
        logs.append(DecisionLog("المرحلة 4 — IFVG","⚠️ لا IFVG",0,"الدخول أقل دقة.",""))

    if ext_liq and ext_liq.rr_ratio>=MIN_RR:
        sc=2 if ext_liq.rr_ratio>=3 else 1; total+=sc
        logs.append(DecisionLog("المرحلة 5 — السيولة الخارجية",
            f"{'BSL' if ext_liq.kind=='ext_high' else 'SSL'} @ {ext_liq.price:.4f} (R:R {ext_liq.rr_ratio:.1f}x)",sc,
            f"الموجة الكاملة {ext_liq.distance_pct:.1f}% من السعر.",
            f"R:R = {ext_liq.rr_ratio:.1f}x"))
    else:
        logs.append(DecisionLog("المرحلة 5 — السيولة الخارجية","⚠️ R:R منخفض",0,
            f"الحد الأدنى {MIN_RR}x.",""))

    grade=("A+" if total>=SCORE_A_PLUS else "A" if total>=SCORE_A else "B" if total>=SCORE_MIN else "SKIP")
    if grade=="SKIP" or not sweep: return None

    entry=eq50 if eq50 else current
    buf=entry*0.004
    sl=(round(sweep.swept_price-buf,4) if bias=="long" else round(sweep.swept_price+buf,4))

    ext_ts=[t for t in targets if t.kind=="ext_liq"]
    wave_tgt=0.0
    if ext_ts:
        wave_tgt=max(t.price for t in ext_ts) if bias=="long" else min(t.price for t in ext_ts)

    return TradeSetup(
        ticker=ticker,bias=bias,entry=round(entry,4),stop_loss=sl,
        targets=targets,pd_array=None,score=total,grade=grade,
        decision_log=logs,dol=dol,smt=smt,sweep=sweep,mss=mss,
        fvg_entry=ifvg,ext_liq=ext_liq,time_ctx=None,
        risk_summary=" | ".join(l.risk_note for l in logs if l.risk_note),
        liquidity_type=liquidity_type,wave_target=wave_tgt,ifvg_eq_50=entry)

# ═══════════════════════════════════════════════════════════
#  MASTER ENGINE
# ═══════════════════════════════════════════════════════════
def run_engine(ticker, smt_ticker,
               htf_interval=None, exec_interval=None,
               entry_interval=None, htf_period=None, exec_period=None):
    df_daily = fetch(ticker, HTF_PERIOD, HTF_INTERVAL)
    df_h4    = fetch(ticker, H4_PERIOD,  H4_INTERVAL)
    df_h1    = fetch(ticker, H1_PERIOD,  H1_INTERVAL)
    df_m15   = fetch(ticker, M15_PERIOD, M15_INTERVAL)
    df_smt   = fetch(smt_ticker, HTF_PERIOD, HTF_INTERVAL)
    swings_d = detect_swings(df_daily, SWING_LB, HTF_CANDLES)

    sweep, liq_lvls, dol, bias, liq_type = stage1_daily_sweep(df_daily, df_h1, df_h4)
    smt_sig, smt_st  = stage2_smt_divergence(df_daily, df_smt, bias)
    mss               = stage3_mss_confirmation(df_h1, sweep, bias)
    ifvg, eq50        = stage4_ifvg_entry(df_h1, df_m15, mss, bias)

    entry_t = eq50 if eq50 else float(df_h1["Close"].iloc[-1])
    sl_t    = (sweep.swept_price*0.996 if sweep and bias=="long"
               else sweep.swept_price*1.004 if sweep else entry_t*0.985)
    targets, ext_liq, wave_tgt = stage5_external_liquidity(df_daily, df_h1, bias, entry_t, sl_t)

    setup = stage6_confidence_gate(sweep,mss,ifvg,eq50,smt_sig,smt_st,
                                   liq_lvls,dol,targets,ext_liq,
                                   df_h1,bias,ticker,liq_type)
    return setup, df_daily, df_h1, df_m15, liq_lvls, swings_d, dol

# ═══════════════════════════════════════════════════════════
#  CHART BUILDER
# ═══════════════════════════════════════════════════════════
def build_chart(df_plot, setup, liq_levels, swings, dol,
                ticker="", n_candles=80, htf_interval="1d"):
    df_plot = df_plot.copy()
    df_plot.index = naive_index(df_plot.index)
    df = df_plot.iloc[-n_candles:].copy()
    x0 = to_naive(df.index[0])
    x1 = to_naive(df.index[-1])
    fig = make_subplots(rows=2,cols=1,row_heights=[0.82,0.18],
                        shared_xaxes=True,vertical_spacing=0.02)

    try:
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            increasing=dict(line=dict(color="#16A34A",width=1),fillcolor="rgba(22,163,74,0.85)"),
            decreasing=dict(line=dict(color="#DC2626",width=1),fillcolor="rgba(220,38,38,0.85)"),
            name="OHLC",showlegend=False),row=1,col=1)
    except Exception: pass

    try:
        vc = ["rgba(22,163,74,0.3)" if c>=o else "rgba(220,38,38,0.3)"
              for c,o in zip(df["Close"],df["Open"])]
        fig.add_trace(go.Bar(x=df.index,y=df["Volume"],marker_color=vc,showlegend=False),row=2,col=1)
    except Exception: pass

    for lv in liq_levels:
        try:
            if lv.price<float(df["Low"].min())*0.97 or lv.price>float(df["High"].max())*1.03: continue
            c = "#16A34A" if lv.kind=="BSL" else "#DC2626"
            if not lv.is_dol: c = c.replace("#16A34A","rgba(22,163,74,0.45)").replace("#DC2626","rgba(220,38,38,0.45)")
            w = 2.2 if lv.is_dol else 0.9
            d = "solid" if lv.is_dol else "dot"
            label = f"{'⬡ DOL ' if lv.is_dol else ''}{lv.kind} [{lv.timeframe}] {lv.price:.2f}"
            fig.add_shape(type="line",x0=x0,y0=lv.price,x1=x1,y1=lv.price,
                          line=dict(color=c,width=w,dash=d),row=1,col=1)
            if lv.is_dol or lv.touches>=2:
                fig.add_annotation(x=x1,y=lv.price,text=f"  {label}",xanchor="left",showarrow=False,
                    font=dict(size=9,color=c,family="monospace"),bgcolor="rgba(15,17,23,0.82)",
                    bordercolor=c,borderwidth=1,borderpad=3,row=1,col=1)
        except Exception: pass

    try:
        sh=[s for s in swings if s.kind=="high" and to_naive(s.timestamp) is not None and to_naive(s.timestamp)>=x0]
        sl_p=[s for s in swings if s.kind=="low" and to_naive(s.timestamp) is not None and to_naive(s.timestamp)>=x0]
        if sh:
            fig.add_trace(go.Scatter(x=[to_naive(s.timestamp) for s in sh],
                y=[s.price*1.002 for s in sh],mode="markers",
                marker=dict(symbol="triangle-down",size=9,color="rgba(220,38,38,0.85)"),
                name="SH",hovertemplate="SH: %{y:.4f}<extra></extra>"),row=1,col=1)
        if sl_p:
            fig.add_trace(go.Scatter(x=[to_naive(s.timestamp) for s in sl_p],
                y=[s.price*0.998 for s in sl_p],mode="markers",
                marker=dict(symbol="triangle-up",size=9,color="rgba(22,163,74,0.85)"),
                name="SL",hovertemplate="SL: %{y:.4f}<extra></extra>"),row=1,col=1)
    except Exception: pass

    if setup:
        def add_lv(price,color,dash,label,width=1.8):
            try:
                fig.add_shape(type="line",x0=x0,y0=price,x1=x1,y1=price,
                              line=dict(color=color,width=width,dash=dash),row=1,col=1)
                fig.add_annotation(x=x1,y=price,text=f"  ◀ {label}: {price:.4f}",
                    xanchor="left",showarrow=False,
                    font=dict(size=10,color=color,family="monospace"),
                    bgcolor="rgba(15,17,23,0.88)",bordercolor=color,
                    borderwidth=1,borderpad=4,row=1,col=1)
            except Exception: pass

        add_lv(setup.entry,"#3B82F6","solid","ENTRY 50% EQ",2.5)
        add_lv(setup.stop_loss,"#EF4444","dot","SL",1.5)

        tp_c={"tp1":"#10B981","tp2":"#34D399","ext_liq":"#F59E0B","tp3":"#6EE7B7"}
        for t in setup.targets:
            add_lv(t.price,tp_c.get(t.kind,"#10B981"),"dash",f"{t.label} R:{t.rr:.1f}x",1.8)

        try:
            if setup.fvg_entry:
                fv=setup.fvg_entry
                fn=to_naive(fv.formed_at); fx0=fn if (fn is not None and fn>=x0) else x0
                fig.add_shape(type="rect",x0=fx0,y0=fv.bottom,x1=x1,y1=fv.top,
                    fillcolor="rgba(59,130,246,0.08)",line=dict(color="rgba(59,130,246,0.5)",width=1.5),row=1,col=1)
                fig.add_annotation(x=fx0,y=(fv.top+fv.bottom)/2,text="  IFVG · 50% EQ",
                    xanchor="left",showarrow=False,
                    font=dict(size=9,color="#3B82F6",family="monospace"),
                    bgcolor="rgba(15,17,23,0.72)",row=1,col=1)
        except Exception: pass

        try:
            if setup.sweep:
                sw=setup.sweep; sn=to_naive(sw.swept_at)
                if sn is not None:
                    sx=sn if sn>=x0 else x0
                    sc="#EF4444" if sw.direction=="buyside" else "#10B981"
                    say=-50 if sw.direction=="buyside" else 50
                    fig.add_annotation(x=sx,y=sw.swept_price,ax=0,ay=say,
                        arrowhead=2,arrowcolor=sc,arrowsize=1.4,arrowwidth=2.5,
                        text=f"{'⬇' if sw.direction=='buyside' else '⬆'} {setup.liquidity_type} Sweep",
                        font=dict(size=9,color=sc,family="monospace"),
                        bgcolor="rgba(15,17,23,0.85)",bordercolor=sc,borderwidth=1,borderpad=3,row=1,col=1)
        except Exception: pass

        try:
            best_rr=max((t.rr for t in setup.targets),default=0)
            wave=f"{setup.wave_target:.2f}" if setup.wave_target else "—"
            bs="▲ شراء" if setup.bias=="long" else "▼ بيع"
            gs={"A+":"⭐⭐⭐","A":"⭐⭐","B":"⭐"}.get(setup.grade,"")
            fig.add_annotation(
                x=df.index[min(3,len(df)-1)],y=float(df["High"].max())*0.993,
                text=f"<b>{bs}</b><br>Grade: {setup.grade} {gs}<br>Score: {setup.score}<br>Best R:R: {best_rr:.1f}x<br>نوع السحب: {setup.liquidity_type}<br>الموجة: {wave}",
                showarrow=False,align="right",
                font=dict(size=10.5,color="#F1F5FB",family="monospace"),
                bgcolor="rgba(15,17,23,0.9)",bordercolor="#3B82F6",borderwidth=1.5,borderpad=10,row=1,col=1)
        except Exception: pass

    grade_s=f" | {setup.grade} | Score {setup.score}" if setup else ""
    fig.update_layout(
        height=660,template="plotly_dark",
        paper_bgcolor="#0F1117",plot_bgcolor="#0F1117",
        font=dict(family="'Tajawal',monospace",color="#8B98A9",size=11),
        margin=dict(l=10,r=170,t=48,b=8),
        xaxis_rangeslider_visible=False,hovermode="x unified",
        title=dict(text=f"<b>{ticker.upper()}</b> — استراتيجية الحبي{grade_s} | {htf_interval}",
                   font=dict(size=13,color="#3B82F6",family="monospace"),x=0.01),
        hoverlabel=dict(bgcolor="#161B27",font=dict(family="monospace",size=11)),
        legend=dict(orientation="h",x=0,y=1.02,bgcolor="rgba(0,0,0,0)",font=dict(size=10)))
    for r in [1,2]:
        fig.update_xaxes(gridcolor="#1E2535",showgrid=True,tickfont=dict(size=10,color="#404858"),
                         zerolinecolor="#1E2535",row=r,col=1)
        fig.update_yaxes(gridcolor="#1E2535",showgrid=True,tickfont=dict(size=10,color="#404858"),
                         side="right",row=r,col=1)
    return fig

# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
def safe_price(val, dec=4):
    try: return "—" if val is None else round(float(val),dec)
    except Exception: return "—"

def extract_row(setup, ticker, smt_ticker):
    if setup is None:
        return {"Ticker":ticker,"SMT":smt_ticker,"Grade":"SKIP","Score":"—",
                "Bias":"—","Entry":"—","SL":"—","TP1":"—","TP2 (Ext)":"—",
                "Best R:R":"—","نوع السيولة":"—","Wave Target":"—",
                "MSS":"—","IFVG 50%":"—",
                "_score_num":0,"_grade_rank":99}
    tps    = [t for t in setup.targets if t.is_tp]
    tp1_v  = safe_price(tps[0].price) if tps else "—"
    ext_ts = [t for t in setup.targets if t.kind=="ext_liq"]
    tp2_v  = safe_price(ext_ts[0].price) if ext_ts else (safe_price(tps[1].price) if len(tps)>1 else "—")
    best_rr= max((t.rr for t in setup.targets),default=0)
    rr_v   = f"1:{best_rr:.1f}" if best_rr>0 else "—"
    return {
        "Ticker":      ticker,
        "SMT":         smt_ticker,
        "Grade":       setup.grade,
        "Score":       str(setup.score),
        "Bias":        "Long" if setup.bias=="long" else "Short",
        "Entry":       safe_price(setup.entry),
        "SL":          safe_price(setup.stop_loss),
        "TP1":         tp1_v,
        "TP2 (Ext)":   tp2_v,
        "Best R:R":    rr_v,
        "نوع السيولة": setup.liquidity_type,
        "Wave Target": safe_price(setup.wave_target,2),
        "MSS":         f"{setup.mss.kind} {setup.mss.direction}" if setup.mss else "—",
        "IFVG 50%":    safe_price(setup.ifvg_eq_50),
        "_score_num":  setup.score,
        "_grade_rank": {"A+":1,"A":2,"B":3,"C":4}.get(setup.grade,99),
    }
