import streamlit as St
import numpy as Np
import pandas as Pd

try:
    import plotly.graph_objects as Go
    HasPlotly = True
except:
    Go = None
    HasPlotly = False

# Config

CommodityRates = {
    "Meat": 0.08, # Meat
    "Fruit": 0.04, # Fruits
    "Vegetable": 0.02, # Vegetables
    "Cereals": 0.12, # Wheat, Rice, Maize
    "Dairy": 0.09, # Milk, Cheese, Butter
    "Vegetable Oils": 0.15, # Palm, Soy, Sunflower
    "Sugar": 0.07, # Raw Sugar
    "Pulses": 0.11 # Beans, Lentils
    }
BaselineTemp = 25
BaselineHumidity = 50
TempCoeff = 1.12

# Page Layout

St.set_page_config(page_title="Food Shelf-Life Simulator", layout="wide")

# Styling

St.markdown("""
    <style>
    .main { background-color: #0f1720; color: #e6eef6; }
    div[data-testid="stMetricValue"] { color: #66d6b6; }
    </style>
    """, unsafe_allow_html=True)

# Functions

def Simulate(Commodity, TempC, Humidity, DaysTotal=90, Points=500):
    KBase = CommodityRates.get(Commodity, 0.03)
    K = KBase * (TempCoeff ** (TempC - BaselineTemp)) * (1 + (Humidity / 100.0))
    Days = Np.linspace(0, DaysTotal, Points)
    Quality = 100.0 * Np.exp(-K * Days)
    return Days, Quality, K

# Metrics Calculation

def GetMetrics(X, Y, Thr):
    ConsumableDay = float(X[Np.where(Y < Thr)[0][0]]) if any(Y < Thr) else float(X[-1])
    Day50 = float(X[Np.where(Y < 50)[0][0]]) if any(Y < 50) else float(X[-1])
    try:
        Auc = float(Np.trapz(Y, X))
    except:
        Dx = X[1:] - X[:-1]
        AvgY = (Y[1:] + Y[:-1]) / 2.0
        Auc = float(Np.sum(AvgY * Dx))
    return ConsumableDay, Day50, Auc

# UI Header

St.title("Shelf-life Simulator")
St.write("See how temperature and humidity affect food quality over time.")

# UI Sidebar

with St.sidebar:
    St.header("Parameters")
    Commodity = St.selectbox("Commodity", list(CommodityRates.keys()))
    St.divider()
    Days = St.slider("Days (Scale of Graph)", 30, 1461, 90)
    TempC = St.slider("Temperature (°C)", 0, 50, 25)
    Humidity = St.slider("Humidity (%)", 0, 100, 50)
    Threshold = St.slider("Threshold (%)", 0, 100, 35)
    St.divider()
    CompareOn = St.checkbox(f"Compare to baseline ({BaselineTemp}°C, {BaselineHumidity}% RH)")

# Simulation

X, Y, K = Simulate(Commodity, TempC, Humidity, DaysTotal=Days)
ConsumableDay, Day50, Auc = GetMetrics(X, Y, Threshold)

# Baseline Compare

if CompareOn:
    XB, YB, _ = Simulate(Commodity, BaselineTemp, BaselineHumidity, DaysTotal=Days)

# UI Metrics

Col1, Col2, Col3 = St.columns(3)
Col1.metric("Consumable (days)", f"{ConsumableDay:.0f}")
Col3.metric("Decay rate (k)", f"{K:.4f}")
Col2.metric("Half-life (days)", f"{Day50:.0f}")

# Graph Chart

if HasPlotly and Go is not None:
    Fig = Go.Figure()
    Fig.add_trace(Go.Scatter(x=X, y=Y, name="Current",
                             line=dict(color='#00FFFF', width=3),
                             fill='tozeroy', fillcolor='rgba(102,214,182,0.08)'))
    if CompareOn:
        Fig.add_trace(Go.Scatter(x=XB, y=YB, name=f"Baseline",
                                 line=dict(color='rgba(200,200,200,0.5)', width=2, dash='dot')))
    Fig.add_hline(y=Threshold, line_dash="dash", line_color="#FF0000",
                  annotation_text=f"Threshold ({Threshold}%)", annotation_position="bottom right")
    Fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        xaxis_title="Days",
        yaxis_title="Quality (%)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=480,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
    )
    St.plotly_chart(Fig, use_container_width=True)
else:
    Df = Pd.DataFrame({"Days": X, "Quality": Y})
    if CompareOn:
        Df["Baseline"] = YB
    Df = Df.set_index("Days")
    St.line_chart(Df)

# About

St.markdown("### About")
St.write(f"**{Commodity}** | {TempC}°C, {Humidity}% RH | Threshold: {Threshold}%")

# How: Formulas

with St.expander("How it works"):
    St.latex(r"K = K_{base} \times 1.12^{(T_c - 20)} \times \left(1 + \frac{H}{100}\right)")
    St.latex(r"Q(t) = 100 \times e^{-K \times t}")
    St.latex(r"Q(t) = 100 \times e^{-K_{base} \times 1.12^{(T_c - 20)} \times \left(1 + \frac{H}{100}\right) \times t}")
    St.write("Exponential decay, simplified model")

# Data Exportation

DfOut = Pd.DataFrame({"Days": X, "Quality": Y})
if CompareOn:
    DfOut["Baseline"] = YB

St.subheader("Data")
St.dataframe(DfOut.head(15), use_container_width=True)

Csv = DfOut.to_csv(index=False)
St.download_button("Download CSV", Csv, file_name="simulation.csv", mime="text/csv")
