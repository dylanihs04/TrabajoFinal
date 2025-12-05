import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import io
import os
import json
import hashlib
import secrets

st.set_page_config(page_title="Simulador Hipotecario - Nuevo Crédito MiVivienda", layout="wide")
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("Login")

    # contador que cambia cada vez que generamos un nuevo captcha
    if "captcha_counter" not in st.session_state:
        st.session_state.captcha_counter = 0

    # keys para los números del captcha según el contador actual
    counter = st.session_state.captcha_counter
    n1_key = f"captcha_num1_{counter}"
    n2_key = f"captcha_num2_{counter}"

    # generar números si aún no existen para este contador
    if n1_key not in st.session_state:
        st.session_state[n1_key] = secrets.randbelow(10) + 1
    if n2_key not in st.session_state:
        st.session_state[n2_key] = secrets.randbelow(10) + 1

    n1 = st.session_state[n1_key]
    n2 = st.session_state[n2_key]
    captcha_pregunta = f"{n1} + {n2}"

    # form key y captcha input key únicos (incluyen el contador)
    form_key = f"login_form_{counter}"
    captcha_input_key = f"captcha_input_{counter}"

    with st.form(form_key):
        # mantengo user_input/pwd_input estáticos para que no tengas que reescribir usuario cada intento
        user = st.text_input("Usuario", key="user_input")
        pwd = st.text_input("Contraseña", type="password", key="pwd_input")

        st.write("*Verificación CAPTCHA:*")
        captcha_respuesta = st.text_input(f"¿Cuánto es {captcha_pregunta}?", key=captcha_input_key)

        submit = st.form_submit_button("Ingresar")

    if submit:
        # validar captcha a partir de la variable local (captcha_respuesta)
        try:
            captcha_valido = int(captcha_respuesta) == (n1 + n2)
        except:
            captcha_valido = False

        if not captcha_valido:
            st.error("❌ CAPTCHA incorrecto. Generando uno nuevo...")
            # incrementa contador para crear widgets nuevos (evita reutilizar estado viejo)
            st.session_state.captcha_counter += 1
            # generar los números para el nuevo contador (se crearán en la próxima ejecución)
            new_counter = st.session_state.captcha_counter
            st.session_state[f"captcha_num1_{new_counter}"] = secrets.randbelow(10) + 1
            st.session_state[f"captcha_num2_{new_counter}"] = secrets.randbelow(10) + 1
            # fuerza recarga para reconstruir formulario limpio
            st.rerun()

        # si captcha válido: validar credenciales
        if user == "jesus" and pwd == "123":
            st.session_state.logged_in = True

            # limpiar todo lo relacionado al captcha para no dejar basura en session_state
            keys_to_remove = [k for k in st.session_state.keys() if k.startswith("captcha_num1_") or k.startswith("captcha_num2_") or k.startswith("captcha_input_")]
            for k in keys_to_remove:
                del st.session_state[k]

            # opcional: limpiar inputs de login
            for k in ("user_input", "pwd_input", "captcha_counter"):
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# ------------------------ SIMULADOR PRINCIPAL ------------------------
def main_app():
    st.markdown("<h1 style='text-align:center;'>🏡 Simulador Hipotecario Profesional</h1>", unsafe_allow_html=True)

    st.write("TU SIMULADOR COMPLETO AQUÍ...")

    st.write("...")
    st.write("... (tu simulador completo) ...")

    # Botón de cerrar sesión
    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.rerun()  # type: ignore

# ------------------------ CONTROL DE PANTALLAS ------------------------
if not st.session_state.logged_in:
    login()
    st.stop()

# botón cerrar sesión en la barra lateral (solo cuando estés dentro)
if st.sidebar.button("Cerrar sesión"):
    st.session_state.logged_in = False
    # limpiar todas las keys relacionadas al login / captcha
    keys_to_remove = [k for k in list(st.session_state.keys()) if k.startswith("captcha_num1_") or k.startswith("captcha_num2_") or k.startswith("captcha_input_")]
    for k in ("user_input","pwd_input"):
        if k in st.session_state:
            keys_to_remove.append(k)
    # también borrar el contador si existe
    if "captcha_counter" in st.session_state:
        keys_to_remove.append("captcha_counter")
    for k in set(keys_to_remove):
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# A PARTIR DE AQUÍ: TU APLICACIÓN 
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.3rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">Simulador Hipotecario - Nuevo Crédito MiVivienda</p>', unsafe_allow_html=True)

def df_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cronograma')
    output.seek(0)
    return output.getvalue()

def calcular_bbp(valor_vivienda_soles):
    UIT_2024 = 5150
    valor_uit = valor_vivienda_soles / UIT_2024
    
    if valor_uit <= 140:
        if valor_vivienda_soles <= 357575:
            return 18500.0
        else:
            return 12850.0
    return 0.0

def validar_financiamiento_maximo(valor_vivienda, cuota_inicial_pct, bonos_totales):
    cuota_inicial_monto = valor_vivienda * (cuota_inicial_pct / 100.0)
    monto_sin_bonos = valor_vivienda - cuota_inicial_monto
    financiamiento_maximo = valor_vivienda * 0.90
    financiamiento_efectivo = monto_sin_bonos - bonos_totales
    return monto_sin_bonos, financiamiento_maximo, financiamiento_efectivo

def calcular_bono_verde_monto(valor_vivienda, porcentaje):
    return (porcentaje / 100.0) * valor_vivienda

dias = {"Mensual": 30, "Trimestral": 90, "Semestral": 180, "Anual": 360}

if 'moneda' not in st.session_state:
    st.session_state.moneda = "PEN"
if 'incluye_bono' not in st.session_state:
    st.session_state.incluye_bono = "No"
if 'bono_tipo' not in st.session_state:
    st.session_state.bono_tipo = None
if 'tipo_tasa' not in st.session_state:
    st.session_state.tipo_tasa = "TN"
if 'tipo_pg' not in st.session_state:
    st.session_state.tipo_pg = "Sin gracia"

st.subheader("📋 Datos del Préstamo")

col1, col2, col3, col4 = st.columns(4)
with col1:
    moneda = st.selectbox("Moneda", ["PEN", "USD"], key='moneda_select')
    st.session_state.moneda = moneda

with col2:
    if st.session_state.moneda == "USD":
        tipo_cambio = st.number_input(
            "Tipo de cambio (S/ por USD)",
            min_value=1.00, max_value=10.00,
            value=3.75, step=0.01,
            format="%.4f"
        )
    else:
        tipo_cambio = 1.0

with col3:
    if st.session_state.moneda == "USD":
        V = st.number_input("Valor de la vivienda (USD)", min_value=10000.0, max_value=250000.0, value=66666.67, step=100.0)
        V_soles = V * tipo_cambio
        UIT_2024 = 5150
        valor_uit = V_soles / UIT_2024
        max_uit = 140
        max_soles = max_uit * UIT_2024
        max_usd = max_soles / tipo_cambio
        
        if V_soles > max_soles:
            st.error(f"⚠ El valor en soles (S/ {V_soles:,.2f}) excede el límite de {max_uit} UIT (S/ {max_soles:,.2f})")
            st.info(f"💡 Valor máximo permitido: USD {max_usd:,.2f}")
    else:
        V = st.number_input("Valor de la vivienda (S/)", min_value=50000.0, max_value=721000.0, value=250000.0, step=1000.0)
        V_soles = V
        
with col4:
    if st.session_state.moneda == "USD":
        st.metric("Valor en Soles", f"S/ {V_soles:,.2f}")

col5, col6, col7 = st.columns(3)
with col5:
    CI = st.number_input("Cuota inicial (%)", min_value=7.5, max_value=90.0, value=20.0, step=0.5,
                        help="Mínimo 7.5% requerido por el Crédito MiVivienda")
with col6:
    n_meses = st.number_input("Plazo (meses)", min_value=60, max_value=300, value=240, step=12)
with col7:
    st.metric("Financiamiento máximo", "90% del valor")

st.divider()
st.subheader("📊 Configuración de Tasa de Interés")

col8, col9, col10, col11 = st.columns(4)
with col8:
    tipo = st.selectbox("Tipo de tasa", ["TN", "TE"], key='tipo_tasa_select')
    st.session_state.tipo_tasa = tipo
with col9:
    tasa = st.number_input("Valor de tasa (%)", min_value=0.0, max_value=50.0, value=7.5, step=0.1)
with col10:
    if st.session_state.tipo_tasa == "TN":
        freq = st.selectbox("Frecuencia de capitalización (TN)", 
                          ["Mensual", "Trimestral", "Semestral", "Anual"])
        plazo_tasa = "Anual"
    else:
        plazo_tasa = st.selectbox("Plazo de tasa efectiva (TE)", 
                                 ["Mensual", "Trimestral", "Semestral", "Anual"])
        freq = None

st.divider()
st.subheader("🎁 Bonos y Subsidios del Nuevo Crédito MiVivienda")

col12, col13 = st.columns(2)
with col12:
    incluye_bono = st.selectbox("¿Incluye bono del FMV?", ["No", "Sí"], key='incluye_bono_select')
    st.session_state.incluye_bono = incluye_bono

bono_tipo = None
bono_bbp = 0.0
bono_verde_pct = 0.0
bono_verde_monto = 0.0

if st.session_state.incluye_bono == "Sí":
    with col13:
        bono_tipo = st.radio("Seleccione tipo de bono", 
                            ["Bono Buen Pagador (BBP)", 
                             "Bono Mi Vivienda Verde", 
                             "Ambos"],
                            key='bono_tipo_radio')
        st.session_state.bono_tipo = bono_tipo
    
    if st.session_state.bono_tipo in ("Bono Buen Pagador (BBP)", "Ambos"):
        bono_bbp = calcular_bbp(V_soles)
        st.success(f"✅ *Bono Buen Pagador calculado:* S/ {bono_bbp:,.2f}")
    
    if st.session_state.bono_tipo in ("Bono Mi Vivienda Verde", "Ambos"):
        st.info("🌱 El Bono Mi Vivienda Verde es del 3% o 4% del valor de la vivienda para viviendas sostenibles certificadas.")
        bono_verde_pct = st.number_input("Porcentaje Bono Mi Vivienda Verde (%)", 
                                        min_value=3.0, max_value=4.0, value=4.0, step=0.01, format="%.2f")
        bono_verde_monto = calcular_bono_verde_monto(V_soles, bono_verde_pct)
        st.success(f"🌱 *Bono Verde calculado:* S/ {bono_verde_monto:,.2f}")

total_bonos = bono_bbp + bono_verde_monto

if total_bonos > 0:
    st.metric("💰 Total de Bonos y Subsidios", f"S/ {total_bonos:,.2f}")

st.divider()
st.subheader("🛡 Seguros y Costos Adicionales")

col14, col15, col16, col17 = st.columns(4)
with col14:
    SD = st.number_input("Seguro Desgravamen (% mensual)", min_value=0.0, max_value=1.0, value=0.055, step=0.001, format="%.3f")
with col15:
    SR = st.number_input("Seguro de Riesgo (% mensual)", min_value=0.0, max_value=1.0, value=0.028, step=0.001, format="%.3f")
with col16:
    CI_ini = st.number_input("Costos iniciales (S/)", min_value=0.0, value=1500.0, step=100.0)
with col17:
    CM = st.number_input("Portes mensuales (S/)", min_value=0.0, value=25.0, step=5.0)

st.divider()
st.subheader("⏸ Periodo de Gracia")
colg1, colg2 = st.columns(2)
with colg1:
    tipo_pg = st.selectbox("Tipo de gracia", 
                          ["Sin gracia", "Gracia total", "Gracia parcial"],
                          key='tipo_pg_select')
    st.session_state.tipo_pg = tipo_pg
with colg2:
    PG = 0
    if st.session_state.tipo_pg in ("Gracia total", "Gracia parcial"):
        PG = st.number_input("Meses de gracia", min_value=0, max_value=6, value=0,
                           help="Máximo 6 meses de gracia")

st.divider()
st.subheader("🏦 Información Adicional")
banco = st.selectbox("Seleccione el banco", 
                    ["BCP", "BBVA", "Interbank", "Scotiabank", 
                     "Banco de la Nación", "Mibanco", "Otros"])

if st.button("🧮 Calcular Simulación", type="primary", use_container_width=True):
    try:
        UIT_2024 = 5150
        valor_uit = V_soles / UIT_2024
        if valor_uit > 140:
            st.error(f"⚠ El valor de la vivienda excede el límite de 140 UIT (S/ 721,000) del Nuevo Crédito MiVivienda.")
            st.stop()
        
        V_calc = V_soles
        CI_monto = V_calc * (CI / 100.0)

        monto_sin_bonos, financiamiento_maximo, financiamiento_efectivo = validar_financiamiento_maximo(
            V_calc, CI, total_bonos
        )
        
        if monto_sin_bonos > financiamiento_maximo:
            porcentaje_cuota_minima = 100 - 90
            st.error(f"⚠ El monto a financiar antes de bonos (S/ {monto_sin_bonos:,.2f}) excede el máximo del 90% (S/ {financiamiento_maximo:,.2f})")
            st.info(f"💡 Aumente la cuota inicial a al menos {porcentaje_cuota_minima:.1f}% del valor de la vivienda.")
            st.stop()

        P = financiamiento_efectivo

        if P <= 0:
            st.warning("⚠ Los bonos y cuota inicial cubren o superan el valor de la vivienda. No se requiere financiamiento.")
            st.stop()

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
                TEM = (1 + TE) ** (dias["Mensual"] / dias[plazo_tasa]) - 1

        if tipo_pg == "Gracia total" and PG > 0:
            P_used = P * (1 + TEM) ** PG
            n_used = n_meses
            inicio_pago_cuota = PG + 1
        elif tipo_pg == "Gracia parcial" and PG > 0:
            P_used = P
            n_used = n_meses
            inicio_pago_cuota = PG + 1
        else:
            P_used = P
            n_used = n_meses
            inicio_pago_cuota = 1

        n_amortizacion = n_meses - PG if PG > 0 else n_meses
        
        if n_amortizacion > 0:
            if TEM == 0:
                C = P_used / n_amortizacion
            else:
                C = P_used * ((TEM * (1 + TEM) ** n_amortizacion) / (((1 + TEM) ** n_amortizacion) - 1))
        else:
            C = 0

        meses = list(range(0, n_meses + 1))
        saldo_ini = [0] * (n_meses + 1)
        interes = [0] * (n_meses + 1)
        amort = [0] * (n_meses + 1)
        sdg = [0] * (n_meses + 1)
        sris = [0] * (n_meses + 1)
        cuota = [0] * (n_meses + 1)
        cuota_total = [0] * (n_meses + 1)
        saldo_fin = [0] * (n_meses + 1)

        current_principal = P
        saldo_ini[0] = saldo_fin[0] = current_principal

        for i in range(1, n_meses + 1):
            saldo_ini[i] = current_principal
            interes[i] = current_principal * TEM

            if i <= PG:
                if tipo_pg == "Gracia total":
                    amort[i] = 0
                    cuota[i] = 0
                    current_principal += interes[i]
                elif tipo_pg == "Gracia parcial":
                    amort[i] = 0
                    cuota[i] = interes[i]
            else:
                cuota[i] = C
                amort[i] = cuota[i] - interes[i]
                if amort[i] < 0:
                    amort[i] = 0
                current_principal -= amort[i]
                if current_principal < 0.01:
                    current_principal = 0

            saldo_fin[i] = current_principal
            sdg[i] = saldo_ini[i] * (SD / 100)
            sris[i] = saldo_ini[i] * (SR / 100)
            cuota_total[i] = cuota[i] + sdg[i] + sris[i] + CM

        df = pd.DataFrame({
            "Mes": meses,
            "Saldo Inicial": saldo_ini,
            "Interés": interes,
            "Amortización": amort,
            "Cuota": cuota,
            "Seguro Desgravamen": sdg,
            "Seguro Riesgo": sris,
            "Portes": [0] + [CM] * n_meses,
            "Cuota Total": cuota_total,
            "Saldo Final": saldo_fin
        })

        flujos = [-CI_ini - CI_monto] + cuota_total[1:]
        
        try:
            TIR = npf.irr(flujos)
            TCEA = (1 + TIR) ** 12 - 1 if TIR is not None and TIR > -1 else None
        except:
            TIR = None
            TCEA = None
        
        try:
            VAN = npf.npv(TEM, flujos) if TEM > 0 else sum(flujos)
        except:
            VAN = None

        st.success("✅ Simulación calculada exitosamente")

        st.subheader("📈 Indicadores Financieros Principales")
        col1, col2, col3, col4 = st.columns(4)

        simbolo = "USD" if moneda == "USD" else "S/"
        monto_display = P / tipo_cambio if moneda == "USD" else P
        col1.metric("Monto Financiado", f"{simbolo} {monto_display:,.2f}")
        col2.metric("Cuota Mensual", f"S/ {C:,.2f}")
        col3.metric("TEM", f"{TEM*100:.4f}%")
        col4.metric("TCEA", f"{TCEA*100:.2f}%" if TCEA else "N/A")

        col5, col6, col7, col8 = st.columns(4)
        total_intereses = sum(interes[1:])
        total_seguros = sum(sdg[1:]) + sum(sris[1:])
        total_pagado = sum(cuota_total[1:]) + CI_ini + CI_monto
        
        col5.metric("Total Intereses", f"S/ {total_intereses:,.2f}")
        col6.metric("Total Seguros", f"S/ {total_seguros:,.2f}")
        col7.metric("Costo Total del Crédito", f"S/ {total_pagado:,.2f}")
        col8.metric("Inversión Inicial", f"S/ {CI_ini + CI_monto:,.2f}")

        st.divider()
        st.subheader("🎁 Resumen de Bonos Aplicados")
        
        resumen_bonos = {
            "Bono Buen Pagador (BBP)": f"S/ {bono_bbp:,.2f}",
            "Bono Mi Vivienda Verde": f"S/ {bono_verde_monto:,.2f} ({bono_verde_pct}%)",
            "*Total Bonos": f"S/ {total_bonos:,.2f}*"
        }
        
        for concepto, valor in resumen_bonos.items():
            st.write(f"• {concepto}: {valor}")

        st.divider()
        st.subheader("📋 Cronograma de Pagos Detallado")
        
        df_display = df.copy()
        for col in df_display.columns:
            if col != "Mes":
                df_display[col] = df_display[col].apply(lambda x: f"S/ {x:,.2f}")
        
        st.dataframe(df_display, use_container_width=True, height=400)

        excel = df_to_excel_bytes(df)
        st.download_button(
            label="📥 Descargar cronograma en Excel",
            data=excel,
            file_name=f"cronograma_hipotecario_{banco}_{V:.0f}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.divider()
        valor_vivienda_display = f"{simbolo} {V:,.2f}"
        if moneda == "USD":
            valor_vivienda_display += f" (S/ {V_soles:,.2f})"
        
        st.info(f"""
        *ℹ Información del Crédito:*
        - Banco: {banco}
        - Moneda: {moneda}
        - Valor vivienda: {valor_vivienda_display}
        - Plazo: {n_meses} meses ({n_meses//12} años)
        - Periodo de gracia: {PG} meses ({tipo_pg})
        - Valor vivienda: {valor_uit:.2f} UIT
        """)

    except Exception as e:
        st.error(f"❌ Error en el cálculo: {str(e)}")
        st.exception(e)

st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p><strong>Simulador Hipotecario v3.0 - Nuevo Crédito MiVivienda</strong></p>
        <p style='font-size: 0.9rem;'>Desarrollado para análisis financiero profesional | 
        Basado en normativa del Fondo MiVivienda 2024-2025</p>
        <p style='font-size: 0.8rem; margin-top: 0.5rem;'>
        ⚠ Los resultados son referenciales. Consulte con su entidad financiera para condiciones exactas.
        </p>
    </div>
""", unsafe_allow_html=True)