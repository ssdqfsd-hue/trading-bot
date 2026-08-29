import streamlit as st
import pandas as pd
import numpy as np
import time

# --- 1. ตั้งค่าหน้าเว็บ Dashboard ---
st.set_page_config(page_title="AI Automated Trading System", layout="wide")
st.title("🤖 ระบบเทรดอัตโนมัติและวิเคราะห์กราฟอัจฉริยะ (Live Dashboard)")

st.markdown("""
ระบบนี้จำลองการทำงานของ AI Trading Bot ที่ดึงข้อมูลราคา วิเคราะห์สัญญาณด้วยเทคนิคอล (EMA & RSI) 
และแสดงผลบนหน้าเว็บแบบเรียลไทม์ พร้อมจำลองการส่งคำสั่งซื้อขายจริง
""")

# --- 2. แถบควบคุมด้านข้าง (Sidebar) ---
st.sidebar.header("⚙️ ตั้งค่าระบบบอทเทรด")
initial_capital = st.sidebar.number_input("ทุนเริ่มต้น (USDT / บาท)", value=50000.0, step=5000.0)
symbol = st.sidebar.selectbox("เลือกคู่เหรียญ/สินทรัพย์", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
trade_amount = st.sidebar.number_input("สัดส่วนเงินลงทุนต่อไม้", value=1000.0)

# เลือกโหมดการทำงาน
trading_mode = st.sidebar.radio("เลือกโหมดการทำงาน:", ["📊 ทดสอบระบบย้อนหลัง (Backtest)", "⚡ รันบอทจำลองเรียลไทม์ (Live Simulation)"])

# --- 3. ฟังก์ชันคำนวณอินดิเคเตอร์และกลยุทธ์ ---
def run_strategy(df):
    # คำนวณ EMA สั้นและยาว
    df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # คำนวณ RSI อย่างง่าย
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # สร้างสัญญาณ (Signal: 1 = ซื้อ, -1 = ขาย, 0 = ถือ)
    df['Signal'] = 0
    buy_condition = (df['EMA_5'] > df['EMA_20']) & (df['RSI'] < 70)
    sell_condition = (df['EMA_5'] < df['EMA_20']) | (df['RSI'] > 75)
    
    df.loc[buy_condition, 'Signal'] = 1
    df.loc[sell_condition, 'Signal'] = -1
    
    return df

# --- 4. การทำงานตามโหมดที่เลือก ---
if trading_mode == "📊 ทดสอบระบบย้อนหลัง (Backtest)":
    if st.sidebar.button("▶️ เริ่มรัน Backtest", type="primary"):
        # สร้างข้อมูลจำลองย้อนหลัง
        np.random.seed(42)
        dates = pd.date_range(start="2026-01-01", periods=100, freq="D")
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        df = pd.DataFrame({'Close': prices}, index=dates)
        
        df = run_strategy(df)
        
        st.subheader(f"📈 กราฟราคาและอินดิเคเตอร์ของ {symbol}")
        st.line_chart(df[['Close', 'EMA_5', 'EMA_20']])
        
        # จำลองการเทรด
        capital = initial_capital
        position = 0
        entry_price = 0.0
        logs = []
        
        for i in range(1, len(df)):
            price = df['Close'].iloc.iloc[i] if hasattr(df['Close'].iloc, 'iloc') else df['Close'].iloc[i]
            sig = df['Signal'].iloc[i]
            date_str = df.index[i].strftime('%Y-%m-%d')
            
            if sig == 1 and position == 0:
                position = 1
                entry_price = price
                logs.append({"วันที่": date_str, "การกระทำ": "BUY (ซื้อ)", "ราคา": f"{entry_price:.2f}", "พอร์ตคงเหลือ": f"{capital:.2f}"})
            elif sig == -1 and position == 1:
                pnl = price - entry_price
                capital += pnl
                logs.append({"วันที่": date_str, "การกระทำ": "SELL (ขาย)", "ราคา": f"{price:.2f}", "พอร์ตคงเหลือ": f"{capital:.2f}"})
                position = 0
                
        st.subheader("📋 บันทึกผลการเทรดอัตโนมัติ")
        if logs:
            st.table(pd.DataFrame(logs))
        else:
            st.info("ไม่มีสัญญาณซื้อขายในรอบนี้")
            
        st.metric("เงินทุนสุทธิสิ้นสุด", f"{capital:,.2f} บาท", f"{capital - initial_capital:+,.2f} บาท")

else:
    # โหมด Live Simulation
    if st.sidebar.button("🚀 เปิดบอทเทรดเรียลไทม์", type="primary"):
        st.success(f"กำลังเชื่อมต่อระบบเพื่อรันบอทเรียลไทม์สำหรับคู่เหรียญ {symbol}...")
        placeholder = st.empty()
        
        # จำลองลูปการทำงานแบบ Real-time 5 รอบ
        current_price = 1500.0
        capital = initial_capital
        
        for step in range(5):
            with placeholder.container():
                # สุ่มจำลองราคาขยับขึ้นลงเล็กน้อย
                current_price += np.random.randn() * 5
                st.metric(label=f"ราคาปัจจุบัน ({symbol})", value=f"${current_price:,.2f}", delta=f"{np.random.randn() * 2:.2f}%")
                
                col1, col2 = st.columns(2)
                col1.info(f"🤖 สถานะ AI: วิเคราะห์ตลาดปกติ (EMA สอดคล้องแนวโน้ม)")
                col2.success(f"💼 มูลค่าพอร์ตจำลอง: ${capital:,.2f}")
                
                st.write(f"🔄 กำลังเช็กรอบเวลาที่ {step + 1}/5 (อัปเดตทุก 3 วินาที)...")
            time.sleep(3)
        st.balloons()
        st.success("จำลองการรันบอทเรียลไทม์ครบกำหนดรอบเรียบร้อยแล้วครับ!")
