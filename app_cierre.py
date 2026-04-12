import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Alaska - Control Total", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stNumberInput"] { width: 100px !important; }
    .resumen-footer { font-size: 16px; font-weight: bold; padding: 12px; border-radius: 8px; background-color: #1e2129; text-align: center; margin-top: 20px; }
    .dif-negativa { color: #ff4b4b; }
    .dif-positiva { color: #2ecc71; }
    .utilidad-card { background-color: #1e2129; padding: 20px; border-radius: 10px; border-left: 5px solid #deff9a; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
def conectar_alaska():
    try:
        info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds).open("Base_Datos_Alaska")
    except: return None

doc = conectar_alaska()

if doc:
    h_prod = doc.worksheet("Productos")
    h_cier = doc.worksheet("Cierres")
    h_util = doc.worksheet("Utilidad")
    
    if 'menu' not in st.session_state:
        datos = h_prod.get_all_records()
        m_temp = {"🍺 Bebidas": {}, "📦 Otros": {}}
        for f in datos:
            cat = f.get('Categoria', '📦 Otros')
            m_temp[cat][f['Producto']] = [float(f.get('Precio', 0)), float(f.get('Costo', 0))]
        st.session_state.menu = m_temp

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 2. ESTRUCTURA DE PESTAÑAS RESTAURADA ---
t_bebidas, t_cocina, t_otros, t_arqueo, t_utilidad = st.tabs(["🍺 Bebidas", "🍳 Cocina", "📦 Otros", "📉 ARQUEO", "💰 UTILIDAD"])

ingresos_totales = 0.0
costos_totales = 0.0

# --- PESTAÑA 1: BEBIDAS ---
with t_bebidas:
    st.subheader("Venta de Bebidas")
    bus = st.text_input("🔍 Buscar bebida...", key=f"bus_{st.session_state.reset_key}").lower()
    for p, v in st.session_state.menu["🍺 Bebidas"].items():
        if bus in p.lower():
            cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"b_{p}_{st.session_state.reset_key}")
            ingresos_totales += (cant * v[0])
            costos_totales += (cant * v[1])

# --- PESTAÑA 2: COCINA (RESTAURADA) ---
with t_cocina:
    st.subheader("Control de Comandas")
    m_cocina = st.number_input("Total Facturado en Cocina (₡)", min_value=0, step=1, key=f"coc_{st.session_state.reset_key}")
    ingresos_totales += m_cocina
    costos_totales += (m_cocina * 0.60) # Costo estimado del 60% para materia prima de cocina
    st.info("Aquí debes ingresar el monto total de las comandas del día.")

# --- PESTAÑA 3: OTROS (RESTAURADA) ---
with t_otros:
    st.subheader("Otros Productos / Snacks")
    for p, v in st.session_state.menu["📦 Otros"].items():
        cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"o_{p}_{st.session_state.reset_key}")
        ingresos_totales += (cant * v[0])
        costos_totales += (cant * v[1])

# --- PESTAÑA 4: ARQUEO ---
with t_arqueo:
    st.header("Arqueo de Caja")
    col1, col2 = st.columns(2)
    efectivo = 0
    with col1:
        for b in [20000, 10000, 5000, 2000, 1000]:
            efectivo += st.number_input(f"₡{b:,}", min_value=0, key=f"bil_{b}_{st.session_state.reset_key}") * b
    with col2:
        for m in [500, 100, 50, 25, 10, 5]:
            efectivo += st.number_input(f"₡{m}", min_value=0, key=f"mon_{m}_{st.session_state.reset_key}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE Móvil", min_value=0, key=f"sn_{st.session_state.reset_key}")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, key=f"tr_{st.session_state.reset_key}")
    fondo = st.number_input("Fondo Inicial", min_value=0, key=f"fd_{st.session_state.reset_key}")

    venta_neta_arqueo = (efectivo + sinpe + tarjetas) - fondo
    diferencia = venta_neta_arqueo - ingresos_totales
    
    color_dif = "dif-positiva" if diferencia >= 0 else "dif-negativa"
    st.markdown(f"""<div class="resumen-footer">Venta Real: ₡{venta_neta_arqueo:,.0f} | Diferencia: <span class="{color_dif}">₡{diferencia:,.0f}</span></div>""", unsafe_allow_html=True)
    
    if st.button("💾 REGISTRAR CIERRE Y UTILIDAD", use_container_width=True):
        ganancia_neta = ingresos_totales - costos_totales
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Guardar en Cierres
        h_cier.append_row([fecha, ingresos_totales, venta_neta_arqueo, diferencia])
        
        # Guardar en Utilidad (A, B, C)
        h_util.append_row([fecha, ingresos_totales, costos_totales, ganancia_neta])
        
        st.success("✅ ¡Cierre y Utilidad guardados exitosamente!")

# --- PESTAÑA 5: UTILIDAD ---
with t_utilidad:
    st.header("Análisis Financiero")
    ganancia_hoy = ingresos_totales - costos_totales
    
    st.markdown(f"""
    <div class='utilidad-card'>
        <p style='margin:0; opacity:0.8;'>Utilidad Neta del Día (Basado en Ventas)</p>
        <h1 style='color: #deff9a; margin:0;'>₡{ganancia_hoy:,.0f}</h1>
        <small>Ingresos (₡{ingresos_totales:,.0f}) - Costos (₡{costos_totales:,.0f})</small>
    </div>
    """, unsafe_allow_html=True)

    try:
        df = pd.DataFrame(h_util.get_all_records())
        if not df.empty:
            st.subheader("Historial de Ganancias (Columna C)")
            # Usamos la última columna que es la de 'Ganancias'
            st.bar_chart(data=df, y=df.columns[-1], color="#deff9a")
    except:
        st.info("La gráfica se actualizará al guardar el primer cierre.")

# --- SIDEBAR: GESTIÓN ---
st.sidebar.header("🛠️ Panel Alaska")
if st.sidebar.button("🧹 LIMPIAR PANTALLA"):
    st.session_state.reset_key += 1
    st.rerun()

if st.sidebar.checkbox("🍔 Administrar Productos"):
    st.sidebar.subheader("Agregar")
    cat_a = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    nom_a = st.sidebar.text_input("Nombre")
    pre_a = st.sidebar.number_input("Precio Venta", min_value=0)
    cos_a = st.sidebar.number_input("Costo Materia Prima", min_value=0)
    if st.sidebar.button("Guardar Nuevo"):
        h_prod.append_row([cat_a, nom_a, pre_a, cos_a])
        if 'menu' in st.session_state: del st.session_state.menu
        st.rerun()
