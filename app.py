from __future__ import annotations

import importlib
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import streamlit as st

from stat_arb_bot.data import load_price_matrix
from stat_arb_bot.market_data import DEFAULT_SYMBOLS, fetch_yahoo_prices, parse_symbol_list
import stat_arb_bot.report as report_module
from stat_arb_bot.scanner import scan_pair_diagnostics, scan_pairs


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
EXPORT_DIR = ROOT / "exports"
APP_BUILD = "symbol-check-2026-06-14"

report_module = importlib.reload(report_module)
build_trade_plan = report_module.build_trade_plan
plans_to_frame = report_module.plans_to_frame


st.set_page_config(page_title="Stat Arb Pair Scanner", layout="wide")

st.markdown(
    """
    <style>
    :root {
      --ink: #202431;
      --muted: #667085;
      --line: #d9e1e8;
      --panel: #f7f9fb;
      --panel-strong: #eef4f7;
      --teal: #0f766e;
      --coral: #be5a43;
      --gold: #b8892d;
      --green: #15803d;
      --red: #b42318;
    }
    .block-container {
      padding-top: 2rem;
      max-width: 1240px;
    }
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
      display: none;
    }
    [data-testid="stSidebar"] {
      background: #f3f6f8;
      border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
      color: var(--ink);
    }
    div.stButton > button:first-child,
    div.stDownloadButton > button:first-child {
      border-radius: 8px;
      border: 1px solid #c8d2dc;
      font-weight: 700;
    }
    div.stButton > button[kind="primary"] {
      background: var(--teal);
      border-color: var(--teal);
    }
    .balance-hero {
      display: grid;
      grid-template-columns: minmax(220px, 1.1fr) minmax(300px, 1.4fr) minmax(220px, 1.1fr);
      gap: 18px;
      align-items: center;
      padding: 26px 28px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, #ffffff 0%, #f7fafb 100%);
      border-radius: 8px;
      margin-bottom: 18px;
    }
    .hero-panel {
      min-height: 142px;
      padding: 18px;
      border-radius: 8px;
      background: var(--panel);
      border: 1px solid #e1e8ee;
    }
    .hero-panel strong {
      display: block;
      font-size: 18px;
      color: var(--ink);
      margin-bottom: 8px;
    }
    .hero-panel span {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }
    .scale-wrap {
      min-height: 200px;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .scale-beam {
      position: absolute;
      top: 102px;
      width: 78%;
      height: 8px;
      background: linear-gradient(90deg, var(--teal), var(--gold), var(--coral));
      border-radius: 999px;
      transform: rotate(-2deg);
      box-shadow: 0 10px 26px rgba(32, 36, 49, 0.12);
    }
    .scale-post {
      position: absolute;
      top: 100px;
      width: 10px;
      height: 86px;
      background: var(--ink);
      border-radius: 999px 999px 0 0;
    }
    .scale-base {
      position: absolute;
      top: 180px;
      width: 118px;
      height: 12px;
      background: var(--ink);
      border-radius: 999px;
    }
    .scale-cup {
      position: absolute;
      top: 124px;
      width: 112px;
      height: 54px;
      border: 4px solid;
      border-top: 0;
      border-radius: 0 0 80px 80px;
      background: rgba(255, 255, 255, 0.75);
    }
    .scale-cup.left {
      left: 10%;
      border-color: var(--teal);
      transform: translateY(8px);
    }
    .scale-cup.right {
      right: 10%;
      border-color: var(--coral);
      transform: translateY(-4px);
    }
    .scale-string {
      position: absolute;
      top: 106px;
      width: 2px;
      height: 32px;
      background: #98a2b3;
    }
    .scale-string.left-a { left: calc(10% + 18px); }
    .scale-string.left-b { left: calc(10% + 92px); }
    .scale-string.right-a { right: calc(10% + 18px); }
    .scale-string.right-b { right: calc(10% + 92px); }
    .hero-title {
      position: absolute;
      top: 0;
      text-align: center;
      padding: 2px 14px 8px;
      background: rgba(255, 255, 255, 0.88);
      border-radius: 8px;
      z-index: 2;
    }
    .hero-title h1 {
      margin: 0;
      font-size: 36px;
      color: var(--ink);
      letter-spacing: 0;
    }
    .hero-title p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }
    .process-strip {
      display: grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr));
      gap: 10px;
      margin: 12px 0 24px;
    }
    .process-step {
      padding: 12px 14px;
      border-radius: 8px;
      border: 1px solid #dbe4ec;
      background: #ffffff;
      color: var(--ink);
      font-weight: 700;
      font-size: 14px;
      text-align: center;
    }
    .plan-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(220px, 1fr));
      gap: 14px;
      margin: 10px 0 22px;
    }
    .plan-card {
      border: 1px solid #dce5ec;
      border-radius: 8px;
      background: #ffffff;
      padding: 16px;
      box-shadow: 0 8px 20px rgba(32, 36, 49, 0.05);
    }
    .plan-card h3 {
      margin: 0 0 10px;
      font-size: 18px;
      color: var(--ink);
    }
    .badge {
      display: inline-block;
      border-radius: 999px;
      padding: 4px 9px;
      font-weight: 800;
      font-size: 12px;
      margin-bottom: 10px;
    }
    .badge-pass { color: #065f46; background: #dff3ea; }
    .badge-wait { color: #92400e; background: #fef3c7; }
    .badge-enter { color: #7f1d1d; background: #fee2e2; }
    .metric-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      padding: 5px 0;
      border-bottom: 1px solid #eef2f6;
      font-size: 13px;
    }
    .metric-row:last-child { border-bottom: 0; }
    .metric-row span:first-child { color: var(--muted); }
    .metric-row span:last-child { color: var(--ink); font-weight: 800; }
    @media (max-width: 900px) {
      .balance-hero,
      .plan-grid,
      .process-strip {
        grid-template-columns: 1fr;
      }
      .scale-wrap { min-height: 210px; }
      .hero-title h1 { font-size: 30px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def status_badge(action: str) -> str:
    if action.startswith("OPEN_POSITION"):
        return "badge-enter"
    if action.startswith("NO_POSITION"):
        return "badge-wait"
    return "badge-pass"


def render_hero() -> None:
    st.markdown(
        """
        <section class="balance-hero">
          <div class="hero-panel">
            <strong>คุณภาพความสัมพันธ์</strong>
            <span>ใช้ correlation, stability และ half-life เพื่อคัดว่าคู่ไหนควรอยู่ใน watchlist.</span>
          </div>
          <div class="scale-wrap" aria-label="two-sided balance scale">
            <div class="hero-title">
              <h1>Stat Arb Pair Scanner</h1>
              <p>ชั่งน้ำหนักคุณภาพของคู่กับจังหวะเข้าเทรด</p>
            </div>
            <div class="scale-beam"></div>
            <div class="scale-post"></div>
            <div class="scale-base"></div>
            <div class="scale-string left-a"></div>
            <div class="scale-string left-b"></div>
            <div class="scale-string right-a"></div>
            <div class="scale-string right-b"></div>
            <div class="scale-cup left"></div>
            <div class="scale-cup right"></div>
          </div>
          <div class="hero-panel">
            <strong>จังหวะเข้าเทรด</strong>
            <span>ใช้ z-score สำหรับเข้า/ออก และใช้ hedge ratio เพื่อกำหนดขนาด order สองฝั่ง.</span>
          </div>
        </section>
        <div class="process-strip">
          <div class="process-step">1 ความสัมพันธ์</div>
          <div class="process-step">2 Half-life</div>
          <div class="process-step">3 ต้นทุน</div>
          <div class="process-step">4 Z-score</div>
          <div class="process-step">5 Hedge ratio</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_plan_cards(plan_df: pd.DataFrame) -> None:
    columns = st.columns(min(3, len(plan_df.head(3))))
    for column, row in zip(columns, plan_df.head(3).itertuples(index=False)):
        values = row._asdict()
        action = str(values["action"])
        z_value = values.get("execution_z_score", values.get("z_score", 0.0))
        hedge_value = values.get("execution_hedge_ratio", values.get("hedge_ratio", 0.0))
        corr_value = values.get("research_correlation", values.get("correlation", 0.0))
        stability_value = values.get("research_stability", values.get("stability", 0.0))
        execution_days = values.get("execution_half_life_days", values.get("execution_half_life", 0.0))
        research_days = values.get("research_half_life_days", values.get("research_half_life", 0.0))
        risk_warning = str(values.get("risk_warning", ""))
        with column:
            with st.container(border=True):
                st.markdown(f"**{values['symbol_a']} / {values['symbol_b']}**")
                st.write(
                    {
                        values["symbol_a"]: values.get("symbol_a_side", "NO_POSITION"),
                        values["symbol_b"]: values.get("symbol_b_side", "NO_POSITION"),
                        "signal": values.get("signal", "NO_POSITION"),
                    }
                )
                if action.startswith("OPEN_POSITION"):
                    st.error(action)
                elif action.startswith("NO_POSITION"):
                    st.warning(action)
                else:
                    st.success(action)
                if risk_warning.startswith("HIGH_RISK"):
                    st.error(risk_warning)
                elif risk_warning.startswith("CAUTION"):
                    st.warning(risk_warning)
                elif risk_warning.startswith("OK"):
                    st.success(risk_warning)
                st.metric("Execution z-score", f"{z_value:.2f}")
                st.metric("Execution hedge ratio", f"{hedge_value:.4f}")
                st.write(
                    {
                        "research correlation": round(corr_value, 3),
                        "research stability": round(stability_value, 3),
                        "research half-life days": round(research_days, 1),
                        "execution half-life days": round(execution_days, 1),
                        "leg notional ratio": round(values.get("leg_notional_ratio", 0.0), 2),
                        "leg A notional": round(values["leg_a_notional"], 2),
                        "leg B notional": round(values["leg_b_notional"], 2),
                    }
                )


def add_workflow_summary(research_tf: str, execution_tf: str) -> None:
    st.markdown(
        f"""
        <div class="process-strip">
          <div class="process-step">เลือกคู่<br>{research_tf}</div>
          <div class="process-step">ความสัมพันธ์<br>Correlation + Stability</div>
          <div class="process-step">เวลาถือคร่าว ๆ<br>Half-life</div>
          <div class="process-step">จังหวะเข้า<br>{execution_tf} Z-score</div>
          <div class="process-step">ขนาด order<br>Hedge ratio</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def timeframe_hours(timeframe: str) -> float:
    if timeframe.endswith("h"):
        return float(timeframe[:-1])
    if timeframe.endswith("d"):
        return float(timeframe[:-1]) * 24
    if timeframe.endswith("wk"):
        return float(timeframe[:-2]) * 24 * 7
    return 1.0


def add_half_life_units(df: pd.DataFrame, prefix: str, timeframe: str) -> pd.DataFrame:
    source = f"{prefix}_half_life"
    if source not in df.columns:
        return df
    hours_per_bar = timeframe_hours(timeframe)
    df[f"{prefix}_half_life_bars"] = df[source]
    df[f"{prefix}_half_life_hours"] = df[source] * hours_per_bar
    df[f"{prefix}_half_life_days"] = df[f"{prefix}_half_life_hours"] / 24
    return df


def filter_requested_symbols(prices: pd.DataFrame, specs) -> pd.DataFrame:
    requested = [spec.symbol for spec in specs]
    available = [symbol for symbol in requested if symbol in prices.columns]
    if not available:
        raise ValueError(
            "ไม่มีข้อมูลราคาสำหรับ symbols ที่พิมพ์ไว้เลย กรุณาตรวจชื่อ symbol หรือเลือก data source ให้ถูกต้อง"
        )
    return prices[available].dropna(how="all")


def build_symbol_status(specs, prices: pd.DataFrame, data_label: str, source_label: str) -> pd.DataFrame:
    rows = []
    for spec in specs:
        if spec.symbol in prices.columns:
            series = prices[spec.symbol].dropna()
            bars = int(series.shape[0])
            if bars > 0:
                status = "OK"
                detail = "โหลดข้อมูลได้"
                first_time = series.index.min()
                last_time = series.index.max()
            else:
                status = "NO_DATA"
                detail = "มี column แต่ไม่มีราคาที่ใช้ได้"
                first_time = None
                last_time = None
        else:
            bars = 0
            status = "MISSING"
            first_time = None
            last_time = None
            if source_label == "Local CSV":
                detail = f"ไม่พบไฟล์ data/{spec.symbol}.csv"
            else:
                detail = "Yahoo/cache ไม่ส่งข้อมูลกลับมา อาจสะกดผิดหรือ provider symbol ไม่รองรับ"

        rows.append(
            {
                "symbol": spec.symbol,
                "provider_symbol": spec.provider_symbol,
                "data": data_label,
                "status": status,
                "bars": bars,
                "first": first_time,
                "last": last_time,
                "detail": detail,
            }
        )
    return pd.DataFrame(rows)


def render_symbol_status(status_df: pd.DataFrame) -> None:
    st.subheader("0 ตรวจ Symbols")
    st.caption("เช็กก่อนว่า symbol ที่พิมพ์ไว้โหลดราคาได้จริงไหม ถ้าขึ้น MISSING หรือ NO_DATA คู่นั้นจะไม่ถูกนำไป scan.")
    visible = ["symbol", "provider_symbol", "data", "status", "bars", "first", "last", "detail"]
    bad = status_df[status_df["status"] != "OK"]
    if not bad.empty:
        bad_symbols = sorted(set(bad["symbol"].astype(str).tolist()))
        st.error(
            "มี symbol ที่โหลดไม่ได้: "
            + ", ".join(bad_symbols)
            + " | ถ้าเป็น Forex บน Yahoo ให้ลองรูปแบบ EURUSD=X หรือใส่แบบ EURUSD=EURUSD=X"
        )
    st.table(status_df[visible])


def render_symbol_summary(status_df: pd.DataFrame, title: str = "ผลตรวจ Symbols") -> None:
    st.markdown(f"**{title}**")
    if status_df.empty:
        st.warning("ยังไม่มีข้อมูลตรวจ symbol")
        return

    latest = status_df.drop_duplicates(subset=["symbol"], keep="last")
    bad = latest[latest["status"] != "OK"]
    if bad.empty:
        st.success("Symbols ทุกตัวโหลดข้อมูลได้")
    else:
        st.error("Symbol ที่โหลดไม่ได้: " + ", ".join(bad["symbol"].astype(str).tolist()))

    lines = []
    for row in latest.itertuples(index=False):
        lines.append(f"{row.symbol}: {row.status} | bars={row.bars} | {row.detail}")
    st.code("\n".join(lines), language="text")


def render_requested_symbol_preview(specs, source_label: str) -> None:
    rows = []
    for spec in specs:
        if source_label == "Local CSV":
            local_file = DATA_DIR / f"{spec.symbol}.csv"
            status = "พบไฟล์ CSV" if local_file.exists() else "ยังไม่พบไฟล์ CSV"
            detail = str(local_file)
        else:
            status = "รอดึงข้อมูลตอนกดเริ่มสแกน"
            detail = "Yahoo symbol: " + spec.provider_symbol
        rows.append(
            {
                "symbol ที่พิมพ์": spec.symbol,
                "provider_symbol": spec.provider_symbol,
                "ตรวจเบื้องต้น": status,
                "detail": detail,
            }
        )

    st.subheader("0 ตรวจ Symbols ก่อนสแกน")
    if not rows:
        st.warning("ยังไม่ได้ใส่ symbol")
        return
    preview_df = pd.DataFrame(rows)
    missing = preview_df[preview_df["ตรวจเบื้องต้น"] == "ยังไม่พบไฟล์ CSV"]
    if not missing.empty:
        st.warning("Local CSV ยังไม่พบไฟล์ของ: " + ", ".join(missing["symbol ที่พิมพ์"].tolist()))
    if source_label == "Yahoo Finance":
        st.info("Yahoo Finance: ตารางนี้คือรายการที่จะส่งไปตรวจตอนกดเริ่มสแกน หลังสแกนแล้วจะขึ้น OK / MISSING / NO_DATA")
    c1, c2, c3 = st.columns(3)
    c1.metric("Symbols", len(preview_df))
    c2.metric("Data source", source_label)
    c3.metric("Ready", len(preview_df) - len(missing))
    st.dataframe(preview_df, use_container_width=True, hide_index=True)


def render_pair_movement_charts(prices: pd.DataFrame, plan_df: pd.DataFrame, lookback: int) -> None:
    st.subheader("4 กราฟดูการวิ่งตามกันของ pair")
    st.caption(
        "กราฟบน normalize ราคาให้เริ่มที่ 100 เพื่อดูว่าทั้งสองตัววิ่งไปทิศเดียวกันแค่ไหน "
        "กราฟล่างดู spread และ z-score เพื่อดูว่าคู่เริ่มแยกออกจากค่าเฉลี่ยหรือยัง."
    )

    for row in plan_df.head(2).itertuples(index=False):
        values = row._asdict()
        symbol_a = values["symbol_a"]
        symbol_b = values["symbol_b"]
        beta = float(values.get("execution_hedge_ratio", values.get("hedge_ratio", 1.0)))
        if symbol_a not in prices.columns or symbol_b not in prices.columns:
            continue

        pair = prices[[symbol_a, symbol_b]].dropna().tail(max(int(lookback) * 3, 120))
        if pair.empty:
            continue

        normalized = pair.divide(pair.iloc[0]).multiply(100)
        spread = pair[symbol_a] - beta * pair[symbol_b]
        spread_mean = spread.rolling(int(lookback)).mean()
        spread_std = spread.rolling(int(lookback)).std(ddof=0).replace(0, pd.NA)
        z_score = (spread - spread_mean) / spread_std
        spread_view = pd.DataFrame(
            {
                "spread": spread,
                "spread_mean": spread_mean,
                "z_score": z_score,
            }
        )

        with st.expander(f"{symbol_a} / {symbol_b} - กราฟการวิ่งตามกัน", expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("ล่าสุด z-score", f"{values.get('execution_z_score', 0.0):.2f}")
            c2.metric("hedge ratio", f"{beta:.4f}")
            c3.metric("half-life days", f"{values.get('execution_half_life_days', 0.0):.1f}")

            st.markdown("**Normalized price: เริ่มต้นที่ 100 เพื่อดูการวิ่งตามกัน**")
            st.line_chart(normalized, use_container_width=True)

            st.markdown("**Spread และ z-score: ใช้ดูการแยกออกจากค่าเฉลี่ย**")
            st.line_chart(spread_view, use_container_width=True)


st.subheader("ตั้งค่า Scan")
with st.container(border=True):
    st.header("ข้อมูล")
    st.caption(f"App build: {APP_BUILD}")
    source = st.radio("Source", ["Yahoo Finance", "Local CSV"], index=1, horizontal=True)
    default_symbols = "EURUSD, GBPUSD, AUDUSD, NZDUSD, XAUUSD, XAGUSD"
    symbols_raw = st.text_area(
        "Symbols",
        value=default_symbols,
        height=120,
        help="ใส่ชื่อย่อ เช่น EURUSD หรือ map ตรง เช่น GOLD=GC=F. Built-ins: "
        + ", ".join(sorted(DEFAULT_SYMBOLS)),
    )
    run = st.button("เริ่มสแกน", type="primary", key="run")
    st.header("1 เลือกคู่")
    research_period = st.selectbox("Research period", ["6mo", "1y", "2y", "5y"], index=1)
    research_interval = st.selectbox("Research timeframe", ["1d", "1wk"], index=0)

    st.header("2 จังหวะเข้าเทรด")
    execution_period = st.selectbox("Execution period", ["1mo", "3mo", "6mo", "1y"], index=0)
    execution_interval = st.selectbox("Execution timeframe", ["1h", "1d"], index=0)
    save_fetched = st.checkbox("บันทึกข้อมูลราคาที่ดึงมาไว้ใน data/", value=True)

    st.header("ตัวกรองความสัมพันธ์")
    research_lookback = st.number_input("Research lookback bars", min_value=20, max_value=500, value=120, step=10)
    min_correlation = st.slider("Min correlation", 0.0, 0.99, 0.75, 0.01)
    min_stability = st.slider("Min stability", 0.0, 1.0, 0.70, 0.01)
    min_half_life = st.number_input("Min half-life", min_value=1.0, max_value=100.0, value=2.0, step=1.0)
    max_half_life = st.number_input("Max half-life", min_value=2.0, max_value=500.0, value=80.0, step=5.0)
    max_cost_bps = st.number_input("Max cost bps", min_value=0.0, max_value=100.0, value=8.0, step=1.0)

    st.header("กติกาเทรด")
    execution_lookback = st.number_input("Execution lookback bars", min_value=20, max_value=500, value=120, step=10)
    entry_z = st.number_input("Entry z-score", min_value=0.5, max_value=5.0, value=2.0, step=0.1)
    exit_z = st.number_input("Exit z-score", min_value=0.0, max_value=3.0, value=0.5, step=0.1)
    stop_z = st.number_input("Stop z-score", min_value=1.0, max_value=8.0, value=3.5, step=0.1)
    notional = st.number_input("Per-pair notional", min_value=100.0, max_value=10_000_000.0, value=10_000.0, step=1000.0)


current_specs = parse_symbol_list(symbols_raw)
render_requested_symbol_preview(current_specs, source)

render_hero()


def load_prices(period_value: str, interval_value: str, label: str, specs) -> pd.DataFrame:
    if source == "Yahoo Finance":
        output_dir = DATA_DIR / label if save_fetched else None
        try:
            prices = fetch_yahoo_prices(specs, period=period_value, interval=interval_value, output_dir=output_dir)
            return prices
        except Exception as exc:
            cached_dir = DATA_DIR / label
            if cached_dir.exists() and any(cached_dir.glob("*.csv")):
                st.warning(f"Yahoo Finance ไม่ส่งข้อมูล {label} ชุดใหม่กลับมา แอปจึงใช้ cached {label} CSV แทน รายละเอียด: {exc}")
                return load_price_matrix(cached_dir)
            if any(DATA_DIR.glob("*.csv")):
                st.warning(
                    "Yahoo Finance ไม่ส่งข้อมูลชุดใหม่กลับมา แอปจึงใช้ root Local CSV แทน "
                    f"รายละเอียด: {exc}"
                )
                return load_price_matrix(DATA_DIR)
            st.warning(f"Yahoo Finance ไม่ส่งข้อมูล {label} และไม่มี cached CSV ให้ใช้ รายละเอียด: {exc}")
            return pd.DataFrame()
    try:
        return load_price_matrix(DATA_DIR)
    except Exception as exc:
        st.warning(f"Local CSV โหลดไม่ได้ รายละเอียด: {exc}")
        return pd.DataFrame()


if run:
    try:
        specs = current_specs
        research_raw_prices = load_prices(research_period, research_interval, f"research_{research_interval}", specs)
        if source == "Local CSV":
            execution_raw_prices = research_raw_prices.copy()
            st.info("โหมด Local CSV ใช้ข้อมูลชุดเดียวกันทั้งการเลือกคู่และจังหวะเข้าเทรด ถ้าต้องการแยก 1d กับ 1h ให้ใช้ Yahoo Finance.")
        else:
            execution_raw_prices = load_prices(execution_period, execution_interval, f"execution_{execution_interval}", specs)

        research_symbol_status = build_symbol_status(specs, research_raw_prices, f"research_{research_interval}", source)
        execution_symbol_status = build_symbol_status(specs, execution_raw_prices, f"execution_{execution_interval}", source)
        symbol_status = pd.concat([research_symbol_status, execution_symbol_status], ignore_index=True)

        add_workflow_summary(research_interval, execution_interval)
        render_symbol_status(symbol_status)
        EXPORT_DIR.mkdir(exist_ok=True)
        symbol_status.to_csv(EXPORT_DIR / "symbol_status.csv", index=False)

        research_prices = filter_requested_symbols(research_raw_prices, specs)
        execution_prices = filter_requested_symbols(execution_raw_prices, specs)

        if len(research_prices.columns) < 2:
            st.error("ต้องมี symbol ที่โหลดข้อมูลได้อย่างน้อย 2 ตัว จึงจะ scan pair ได้")
            st.stop()

        pairs = scan_pairs(
            research_prices,
            lookback=int(research_lookback),
            min_correlation=float(min_correlation),
            min_stability=float(min_stability),
            min_half_life=float(min_half_life),
            max_half_life=float(max_half_life),
            max_cost_bps=float(max_cost_bps),
        )
        diagnostics = scan_pair_diagnostics(
            research_prices,
            lookback=int(research_lookback),
            min_correlation=float(min_correlation),
            min_stability=float(min_stability),
            min_half_life=float(min_half_life),
            max_half_life=float(max_half_life),
            max_cost_bps=float(max_cost_bps),
        )

        st.subheader("1 ข้อมูลสำหรับเลือกคู่")
        st.caption(
            f"Research TF: {research_interval} | {research_prices.index.min()} ถึง {research_prices.index.max()} | "
            f"{len(research_prices)} bars | {len(research_prices.columns)} symbols"
        )
        st.line_chart(research_prices.dropna(how="all"))

        st.subheader("2 คู่ที่ผ่านจาก Research timeframe")
        st.caption(
            f"เลือกคู่ด้วย {research_interval} แล้วแยกดูจังหวะเข้าเทรดด้วย {execution_interval}."
        )
        if not diagnostics.empty:
            st.dataframe(
                diagnostics[
                    [
                        "symbol_a",
                        "symbol_b",
                        "correlation",
                        "stability",
                        "relationship_ok",
                        "half_life",
                        "half_life_ok",
                        "cost_bps",
                        "cost_ok",
                        "latest_z",
                        "hedge_ratio",
                        "final_status",
                        "score",
                    ]
                ],
                use_container_width=True,
            )

        if pairs.empty:
            st.warning("ยังไม่มีคู่ที่ผ่านตัวกรอง ลองลด min correlation หรือขยายช่วง half-life.")
        else:
            st.subheader("คู่ที่ผ่านตัวกรองทั้งหมด")
            st.dataframe(pairs, use_container_width=True)

            plans = []
            research_rows = []
            for row in pairs.head(10).itertuples(index=False):
                if row.symbol_a not in execution_prices.columns or row.symbol_b not in execution_prices.columns:
                    continue
                plans.append(
                    build_trade_plan(
                        execution_prices,
                        row.symbol_a,
                        row.symbol_b,
                        lookback=int(execution_lookback),
                        entry_z=float(entry_z),
                        exit_z=float(exit_z),
                        stop_z=float(stop_z),
                        notional=float(notional),
                        cost_bps=float(row.cost_bps),
                    )
                )
                research_rows.append(row._asdict())

            plan_df = plans_to_frame(plans)
            research_df = pd.DataFrame(research_rows)
            if not plan_df.empty and not research_df.empty:
                plan_df = plan_df.rename(
                    columns={
                        "z_score": "execution_z_score",
                        "hedge_ratio": "execution_hedge_ratio",
                        "correlation": "execution_correlation",
                        "half_life": "execution_half_life",
                        "stability": "execution_stability",
                    }
                )
                plan_df["research_timeframe"] = research_interval
                plan_df["execution_timeframe"] = execution_interval
                plan_df["research_correlation"] = research_df["correlation"].values
                plan_df["research_stability"] = research_df["stability"].values
                plan_df["research_half_life"] = research_df["half_life"].values
                plan_df["research_score"] = research_df["score"].values
                plan_df = add_half_life_units(plan_df, "research", research_interval)
                plan_df = add_half_life_units(plan_df, "execution", execution_interval)

            EXPORT_DIR.mkdir(exist_ok=True)
            pairs_path = EXPORT_DIR / "candidate_pairs.csv"
            diagnostics_path = EXPORT_DIR / "pair_diagnostics.csv"
            symbol_status_path = EXPORT_DIR / "symbol_status.csv"
            plan_path = EXPORT_DIR / "trade_plan.csv"
            json_path = EXPORT_DIR / "trade_plan.json"
            pairs.to_csv(pairs_path, index=False)
            diagnostics.to_csv(diagnostics_path, index=False)
            symbol_status.to_csv(symbol_status_path, index=False)
            plan_df.to_csv(plan_path, index=False)
            plan_df.to_json(json_path, orient="records", indent=2)

            render_symbol_summary(symbol_status, "ตรวจ Symbols ก่อนดูแผนเทรด")
            st.subheader("3 จังหวะเข้าเทรดและแผนสำหรับ robot")
            st.caption(
                f"คำนวณ z-score, action และ hedge ratio ด้วย {execution_interval}. "
                f"ส่วนการเลือกคู่ใช้ {research_interval}."
            )
            if plan_df.empty:
                st.warning("คู่ที่เลือกมายังมีข้อมูล execution timeframe ไม่พอ.")
            else:
                render_plan_cards(plan_df)
                preferred_columns = [
                    "symbol_a",
                    "symbol_b",
                    "signal",
                    "symbol_a_side",
                    "symbol_b_side",
                    "entry_reason",
                    "action",
                    "execution_timeframe",
                    "execution_z_score",
                    "execution_hedge_ratio",
                    "execution_half_life_bars",
                    "execution_half_life_hours",
                    "execution_half_life_days",
                    "research_timeframe",
                    "research_correlation",
                    "research_stability",
                    "research_half_life_bars",
                    "research_half_life_hours",
                    "research_half_life_days",
                    "entry_rule",
                    "exit_rule",
                    "stop_rule",
                    "leg_a_notional",
                    "leg_b_notional",
                    "leg_notional_ratio",
                    "risk_warning",
                ]
                visible_columns = [column for column in preferred_columns if column in plan_df.columns]
                st.dataframe(plan_df[visible_columns], use_container_width=True)
                st.download_button("Download trade_plan.csv", plan_df.to_csv(index=False), "trade_plan.csv")
                st.download_button("Download trade_plan.json", json_path.read_text(), "trade_plan.json")
                render_pair_movement_charts(execution_prices, plan_df, int(execution_lookback))

            for plan in plans[:3]:
                with st.expander(f"{plan.symbol_a} / {plan.symbol_b}: {plan.action}"):
                    st.write(
                        {
                            "signal": plan.signal,
                            plan.symbol_a: plan.symbol_a_side,
                            plan.symbol_b: plan.symbol_b_side,
                            "entry_reason": plan.entry_reason,
                            "z_score": round(plan.z_score, 3),
                            "hedge_ratio": round(plan.hedge_ratio, 4),
                            "correlation": round(plan.correlation, 4),
                            "half_life": round(plan.half_life, 2),
                            "stability": round(plan.stability, 4),
                            "suggested_legs": plan.suggested_legs,
                            "risk_warning": plan_df.loc[
                                (plan_df["symbol_a"] == plan.symbol_a) & (plan_df["symbol_b"] == plan.symbol_b),
                                "risk_warning",
                            ].iloc[0],
                            "entry_rule": plan.entry_rule,
                            "exit_rule": plan.exit_rule,
                            "stop_rule": plan.stop_rule,
                        }
                    )

            st.success(f"บันทึกไฟล์ export แล้วที่ {EXPORT_DIR}")
    except Exception as exc:
        st.error(str(exc))
else:
    st.info("เลือก symbols แล้วกดเริ่มสแกน.")
