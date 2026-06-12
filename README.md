# Statistical Arbitrage Bot

โปรเจกต์นี้เป็นโครง bot สำหรับหาและทดสอบคู่สินทรัพย์แบบ statistical arbitrage โดยเน้นความปลอดภัยก่อนต่อ live trading จริง

สิ่งที่มีให้:

- หา pair ที่ correlation สูง
- วัด hedge ratio และ spread
- ตรวจว่า spread มีแนวโน้มกลับค่าเฉลี่ยหรือไม่
- คัดกรองความเสถียรของความสัมพันธ์
- ประเมินต้นทุน spread/commission แบบง่าย
- backtest กลยุทธ์ z-score mean reversion
- paper trading loop พร้อม broker interface สำหรับต่อยอด

## โครงข้อมูลราคา

ใส่ไฟล์ CSV ไว้ในโฟลเดอร์ `data/` โดยตั้งชื่อไฟล์เป็นชื่อสินทรัพย์ เช่น:

```text
data/EURUSD.csv
data/GBPUSD.csv
data/XAUUSD.csv
data/XAGUSD.csv
```

แต่ละไฟล์ควรมี column อย่างน้อย:

```csv
timestamp,close
2026-01-01 00:00:00,1.1000
2026-01-01 01:00:00,1.1005
```

ถ้ามี bid/ask สามารถใส่เพิ่มได้:

```csv
timestamp,bid,ask,close
```

## ติดตั้ง

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

หมายเหตุสำหรับ Mac mini:

- โปรเจกต์นี้ใช้ `Python 3.8` ได้ แต่ต้อง pin `multitasking<0.0.12` เพื่อให้ `yfinance` ทำงานได้
- ถ้าต้องการเปิดจาก Desktop ให้รัน:

```bash
./install_desktop_app.command
```

หลังจากนั้นจะได้ทั้ง:

- `Stat Arb Pair Scanner.app`
- `Stat Arb Pair Scanner.command`

โดย `.app` และ `.command` จะเรียก launcher ชุดเดียวกัน และถ้า `.venv` ยังไม่พร้อม ตัว launcher จะสร้าง environment และติดตั้ง dependency ให้อัตโนมัติ

## หา pair

ถ้ายังไม่มีข้อมูลจริง สร้างข้อมูลทดลองก่อน:

```bash
python scripts/generate_sample_data.py
```

```bash
python scripts/scan_pairs.py --data-dir data --output pairs.csv
```

## เปิดแอป

```bash
streamlit run app.py
```

แอปจะดึงราคาจาก Yahoo Finance หรืออ่าน CSV ใน `data/` แล้วสร้างไฟล์สำหรับ robot trading ที่:

```text
exports/candidate_pairs.csv
exports/pair_diagnostics.csv
exports/trade_plan.csv
exports/trade_plan.json
```

The app scans in this order:

1. Check `correlation` and `stability` to decide whether the pair relationship is good enough.
2. Check `half_life` to decide whether the spread reverts in a useful holding period.
3. Check estimated `cost_bps`.
4. Use `z_score` for entry, exit, and stop planning.
5. Use `hedge_ratio` for suggested long/short sizing.

## Backtest pair

```bash
python scripts/backtest_pair.py --data-dir data --symbol-a EURUSD --symbol-b GBPUSD
```

## Paper trading

```bash
python scripts/paper_trade.py --data-dir data --symbol-a EURUSD --symbol-b GBPUSD
```

## Live trading

ไฟล์ `stat_arb_bot/broker.py` มี interface สำหรับต่อ broker จริง เช่น MT5, OANDA, Binance หรือ Interactive Brokers

ก่อนเปิดเงินจริง ควรเพิ่ม:

- order confirmation
- max daily loss
- max open exposure
- max slippage
- kill switch
- broker-specific lot sizing
- logging ลง database
- alert เมื่อ order เข้าไม่ครบทั้งสองฝั่ง

นี่ไม่ใช่คำแนะนำการลงทุน และควรทดสอบด้วยบัญชี demo ก่อนเสมอ
