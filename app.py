import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import io

# Configuración de página
st.set_page_config(page_title="Simulador Hipotecario", page_icon="🏠", layout="wide")

# Estilos personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🏠 Simulador Hipotecario Profesional</p>', unsafe_allow_html=True)

def df_to_excel_bytes(df):
    """Convierte un DataFrame a bytes de Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cronograma')
    output.seek(0)
    return output.getvalue()

def calcular_bbp(valor_vivienda):
    """Calcula el Bono de Buen Pagador según el valor de la vivienda"""
    if 58800 <= valor_vivienda < 84100:
        return 17700
    elif 84100 <= valor_vivienda < 125900:
        return 14600
    elif 125900 <= valor_vivienda < 209800:
        return 13000
    elif 209800 <= valor_vivienda <= 310800:
        return 6400
    return 0

dias = {"Mensual": 30, "Trimestral": 90, "Semestral": 180, "Anual": 360}

# Formulario principal
with st.form("formulario_hipoteca"):
    st.subheader("📋 Datos del Préstamo")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        V = st.number_input("💰 Valor de la vivienda", min_value=0.0, value=150000.0, step=1000.0)
    with col2:
        CI = st.number_input("📊 Cuota inicial (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    with col3:
        n_meses = st.number_input("📅 Plazo (meses)", min_value=1, max_value=500, value=120, step=1)
    with col4:
        moneda = st.selectbox("💵 Moneda", ["USD", "PEN"])
    
    st.divider()
    st.subheader("📈 Configuración de Tasa de Interés")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        tipo = st.selectbox("Tipo de tasa", ["TN", "TE"])
    with col6:
        tasa = st.number_input("Valor de tasa (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.1)
    with col7:
        if tipo == "TN":
            freq = st.selectbox("Frecuencia de capitalización", ["Mensual", "Trimestral", "Semestral", "Anual"])
            plazo_tasa = "Anual"
        else:
            plazo_tasa = st.selectbox("Plazo de tasa efectiva", ["Mensual", "Trimestral", "Semestral", "Anual"])
            freq = None
    with col8:
        PG = st.number_input("Periodo de gracia (meses)", min_value=0, max_value=6, value=0, step=1)
    
    st.divider()
    st.subheader("🎁 Bonos y Seguros")
    
    col9, col10, col11, col12 = st.columns(4)
    with col9:
        tipo_pg = st.selectbox("Tipo de gracia", ["ninguna", "parcial", "total"])
    with col10:
        BBP = calcular_bbp(V)
        st.number_input("Bono Buen Pagador", value=float(BBP), disabled=True)
    with col11:
        BTP = st.number_input("Bono Techo Propio", min_value=0.0, value=1000.0, step=100.0)
    with col12:
        SD = st.number_input("Seguro Desgravamen (%)", min_value=0.0, max_value=100.0, value=0.25, step=0.01)
    
    st.divider()
    st.subheader("💳 Costos Adicionales")
    
    col13, col14, col15, col16 = st.columns(4)
    with col13:
        SR = st.number_input("Seguro de Riesgo (%)", min_value=0.0, max_value=100.0, value=0.12, step=0.01)
    with col14:
        CI_ini = st.number_input("Costo inicial", min_value=0.0, value=300.0, step=10.0)
    with col15:
        CM = st.number_input("Costo mensual", min_value=0.0, value=10.0, step=1.0)
    with col16:
        st.write("")
    
    enviar = st.form_submit_button("🚀 Calcular Simulación", use_container_width=True)

if enviar:
    try:
        # Conversión de moneda si es necesario
        V_calc = V * 3.60 if moneda == "USD" else V
        
        # Cálculos principales
        CI_monto = V_calc * (CI / 100)
        P = V_calc - CI_monto - BBP - BTP
        
        # Cálculo de TEM (Tasa Efectiva Mensual)
        if tipo == "TN":
            TNA = tasa / 100
            m = {"Mensual": 12, "Trimestral": 4, "Semestral": 2, "Anual": 1}[freq]
            n = dias["Mensual"] / dias[freq]
            TEM = (1 + (TNA / m)) ** n - 1
        else:
            TE = tasa / 100
            if plazo_tasa == "Mensual":
                TEM = TE
            else:
                n1 = dias["Mensual"]
                n2 = dias[plazo_tasa]
                TEM = (1 + TE) ** (n1 / n2) - 1
        
        # Ajuste por periodo de gracia
        if PG > 0 and tipo_pg != "ninguna":
            P_used = P * (1 + TEM) ** PG
        else:
            P_used = P
        
        # Cálculo de cuota
        n_used = n_meses
        C = P_used * ((TEM * (1 + TEM) ** n_used) / (((1 + TEM) ** n_used) - 1))
        
        # Inicialización de listas
        meses = list(range(0, n_meses + 1))
        saldo_ini = [P] + [0] * n_meses
        interes = [0] + [0] * n_meses
        amort = [0] + [0] * n_meses
        sdg = [0] + [0] * n_meses
        sris = [0] + [0] * n_meses
        cuota = [0] + [0] * n_meses
        cuota_total = [0] + [0] * n_meses
        saldo_fin = [P] + [0] * n_meses
        
        # Generación del cronograma
        for i in range(1, n_meses + 1):
            saldo_ini[i] = saldo_fin[i - 1]
            interes[i] = saldo_ini[i] * TEM
            
            if tipo_pg == "total" and i <= PG:
                amort[i] = 0
                cuota[i] = interes[i]
            elif tipo_pg == "parcial" and i <= PG:
                amort[i] = C * 0.3
                cuota[i] = interes[i] + amort[i]
            else:
                amort[i] = C - interes[i]
                cuota[i] = C
            
            sdg[i] = saldo_ini[i] * (SD / 100)
            sris[i] = saldo_ini[i] * (SR / 100)
            cuota_total[i] = cuota[i] + sdg[i] + sris[i]
            saldo_fin[i] = saldo_ini[i] - amort[i]
        
        # Creación del DataFrame
        df = pd.DataFrame({
            "Mes": meses,
            "Saldo Inicial": saldo_ini,
            "Interés": interes,
            "Amortización": amort,
            "Seguro Desgravamen": sdg,
            "Seguro Riesgo": sris,
            "Cuota Base": cuota,
            "Cuota Total": cuota_total,
            "Saldo Final": saldo_fin
        })
        
        # Formato de columnas numéricas
        for col in df.columns[1:]:
            df[col] = df[col].round(2)
        
        # Cálculos financieros
        flujos = [-CI_ini - P] + cuota_total[1:]
        TIR = npf.irr(flujos)
        TCEA = (1 + TIR) ** 12 - 1 if TIR is not None else None
        VAN = npf.npv(TEM, flujos)
        
        # Mostrar resultados
        st.success("✅ Simulación calculada exitosamente")
        
        st.subheader("📊 Indicadores Financieros")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            st.metric("💰 Monto Financiado", f"S/ {P:,.2f}")
        with col_m2:
            st.metric("📅 Cuota Mensual", f"S/ {C:,.2f}")
        with col_m3:
            st.metric("📈 TEM", f"{TEM * 100:.4f}%")
        with col_m4:
            st.metric("📊 TCEA", f"{TCEA * 100:.2f}%" if TCEA else "N/A")
        
        col_m5, col_m6, col_m7, col_m8 = st.columns(4)
        
        with col_m5:
            st.metric("💵 TIR", f"{TIR * 100:.4f}%" if TIR else "N/A")
        with col_m6:
            st.metric("📉 VAN", f"S/ {VAN:,.2f}" if VAN is not None else "N/A")
        with col_m7:
            total_intereses = sum(interes[1:])
            st.metric("💸 Total Intereses", f"S/ {total_intereses:,.2f}")
        with col_m8:
            total_pagado = sum(cuota_total[1:])
            st.metric("💰 Total a Pagar", f"S/ {total_pagado:,.2f}")
        
        st.divider()
        st.subheader("📋 Cronograma de Pagos")
        st.dataframe(df, use_container_width=True, height=400)
        
        # Botón de descarga
        excel = df_to_excel_bytes(df)
        st.download_button(
            "⬇️ Descargar cronograma en Excel",
            data=excel,
            file_name="cronograma_hipotecario.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Error en el cálculo: {str(e)}")
        st.info("Por favor, verifica que todos los datos ingresados sean correctos.")

# Pie de página
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>📌 Simulador Hipotecario v2.0 | Desarrollado para análisis financiero</p>
    </div>
""", unsafe_allow_html=True)