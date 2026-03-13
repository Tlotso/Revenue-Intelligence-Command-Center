import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# --- PAGE CONFIG ---
st.set_page_config(page_title="Revenue Intelligence", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    df = pd.read_csv("data_summarized.csv")
    df['Order.Date'] = pd.to_datetime(df['Order.Date'])
    return df

df = load_data()
monthly = df.set_index('Order.Date')[['Sales', 'Profit']].resample('MS').sum().reset_index()

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Command Controls")
horizon = st.sidebar.selectbox("Time Horizon", [1, 3, 6], index=2, format_func=lambda x: f"{x} Months")
scenario = st.sidebar.radio("Forecast Scenario", ["Worst Case (-20%)", "Standard (Base)", "Best Case (+25%)"], index=1)

# --- ANALYTICS ENGINE ---
def get_metrics(months, scenario_label):
    curr, prev = monthly.iloc[-months:], monthly.iloc[-(2*months):-months]
    
    # Historicals
    c_rev, p_rev = curr['Sales'].sum(), prev['Sales'].sum()
    c_prof, p_prof = curr['Profit'].sum(), prev['Profit'].sum()
    
    # Advanced Forecast (Holt-Winters)
    model = ExponentialSmoothing(monthly['Sales'], trend='add', seasonal='add', seasonal_periods=12).fit()
    base_f = model.forecast(months).sum()
    
    # Scenario Logic
    if "Worst" in scenario_label: base_f *= 0.80
    elif "Best" in scenario_label: base_f *= 1.25
    
    return c_rev, p_rev, c_prof, p_prof, base_f

c_rev, p_rev, c_prof, p_prof, forecast = get_metrics(horizon, scenario)

# --- DASHBOARD UI ---
st.title("📊 Revenue Intelligence Command Center")
st.markdown(f"### Strategy View: {horizon}-Month Horizon | {scenario}")

# Row 1: The Scorecard
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${c_rev:,.0f}", f"{(c_rev-p_rev)/p_rev:.1%}")
col2.metric("Net Profit", f"${c_prof:,.0f}", f"{(c_prof-p_prof)/p_prof:.1%}")
col3.metric("Profit Margin", f"{(c_prof/c_rev):.1%}", f"{(c_prof/c_rev)-(p_prof/p_rev):.2%}", delta_color="normal")
col4.metric("Projected Pipeline", f"${forecast:,.0f}", help="Forecast based on Holt-Winters Exponential Smoothing")

# Row 2: Visualizing the Trend
st.divider()
fig = go.Figure()
fig.add_trace(go.Scatter(x=monthly['Order.Date'], y=monthly['Sales'], name="Historical Revenue", line=dict(color='#2980B9')))
fig.update_layout(template="plotly_white", height=400, title="Revenue Momentum & Forecast")
st.plotly_chart(fig, use_container_width=True)

# --- CALL TO ACTION ---
st.error(f"**STRATEGIC ACTION:** Current {scenario} suggests a focus on {'cost cutting' if 'Worst' in scenario else 'scaling operations'}.")