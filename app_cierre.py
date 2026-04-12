import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Alaska - Control de Utilidad", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stNumberInput"] { width: 180px !important; }
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
    h_util = doc.worksheet("Utilidad") # Nueva pestaña solicitada
    
    if 'menu' not in st.session_state:
        datos = h_prod.get_all_records()
        m_temp = {"🍺 Bebidas": {}, "📦 Otros": {}}
        for f in datos:
            cat = f.get('Categoria', '📦 Otros')
            m_temp[cat][f['Producto']] = [float(f.get('Precio', 0)), float(f.get('Costo', 0))]
        st.session_state.menu = m_temp

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 2. ESTRUCTURA DE PESTAÑAS ---
t_ventas, t_arqueo, t_ganancia = st.tabs(["🛒 VENTAS", "📉 ARQUEO", "💰 UTILIDAD"])

ingresos_totales = 0.0
costos_totales = 0.0

with t_ventas:
    # --- SECCIÓN BEBIDAS ---
    st.subheader("Bebidas")
    bus = st.text_input("🔍 Buscar producto...", key=f"b_{st.session_state.reset_key}").lower()
    for p, v in st.session_state.menu["🍺 Bebidas"].items():
        if bus in p.lower():
            cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"v_{p}_{st.session_state.reset_key}")
            ingresos_totales += (cant * v[0])
            costos_totales += (cant * v[1])
    
    st.divider()
    # --- SECCIÓN COCINA ---
    st.subheader("Cocina")
    m_cocina = st.number_input("Total Comandas Cocina (₡)", min_value=0, step=1, key=f"coc_{st.session_state.reset_key}")
    ingresos_totales += m_cocina
    costos_totales += (m_cocina * 0.60) # 60% costo sugerido

    st.divider()
    # --- SECCIÓN OTROS ---
    st.subheader("Otros")
    for p, v in st.session_state.menu["📦 Otros"].items():
        cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"o_{p}_{st.session_state.reset_key}")
        ingresos_totales += (cant * v[0])
        costos_totales += (cant * v[1])

with t_arqueo:
    st.header("Arqueo de Caja")
    col1, col2 = st.columns(2)
    efectivo = 0
    with col1:
        for b in [20000, 10000, 5000, 2000, 1000]:
            efectivo += st.number_input(f"₡{b:,}", min_value=0, key=f"bi_{b}_{st.session_state.reset_key}") * b
    with col2:
        for m in [500, 100, 50, 25, 10, 5]:
            efectivo += st.number_input(f"₡{m}", min_value=0, key=f"mo_{m}_{st.session_state.reset_key}") * m

    st.divider()
    sinpe = st.number_input("SINPE Móvil", min_value=0, key=f"sn_{st.session_state.reset_key}")
    tarjetas = st.number_input("Tarjetas", min_value=0, key=f"tr_{st.session_state.reset_key}")
    fondo = st.number_input("Fondo Inicial", min_value=0, key=f"fd_{st.session_state.reset_key}")

    venta_neta = (efectivo + sinpe + tarjetas) - fondo
    diferencia = venta_neta - ingresos_totales
    
    color_dif = "dif-positiva" if diferencia >= 0 else "dif-negativa"
    st.markdown(f"""<div class="resumen-footer">Venta Real: ₡{venta_neta:,.0f} | Diferencia: <span class="{color_dif}">₡{diferencia:,.0f}</span></div>""", unsafe_allow_html=True)
    
    if st.button("💾 REGISTRAR CIERRE Y UTILIDAD", use_container_width=True):
        ganancia_neta = ingresos_totales - costos_totales
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # 1. Guardar en Cierres (Arqueo)
        h_cier.append_row([fecha, ingresos_totales, venta_neta, diferencia])
        
        # 2. Guardar en Utilidad (Lo que pediste: A, B, C)
        # Nota: He añadido la fecha al inicio para que la gráfica tenga tiempo
        h_util.append_row([fecha, ingresos_totales, costos_totales, ganancia_neta])
        
        st.success("✅ Datos enviados a 'Utilidad' y 'Cierres'.")

with t_ganancia:
    st.header("📊 Análisis de Ganancias")
    ganancia_ahora = ingresos_totales - costos_totales
    
    st.markdown(f"""
    <div class='utilidad-card'>
        <p style='margin:0; opacity:0.8;'>Ganancia Neta Calculada (Hoy)</p>
        <h1 style='color: #deff9a; margin:0;'>₡{ganancia_ahora:,.0f}</h1>
        <small>Fórmula: Ingreso (₡{ingresos_totales:,.0f}) - Costo (₡{costos_totales:,.0f})</small>
    </div>
    """, unsafe_allow_html=True)

    try:
        # Extraemos datos de la pestaña UTILIDAD
        registros = h_util.get_all_records()
        if registros:
            df = pd.DataFrame(registros)
            # El usuario pidió Columna C (Ganancias)
            # Asumimos que la columna se llama 'Ganancias' o es la tercera columna de datos
            st.subheader("Historial de Ganancia Neta")
            col_ganancia = df.columns[3] if len(df.columns) > 3 else df.columns[-1]
            st.bar_chart(data=df, y=col_ganancia, color="#deff9a")
        else:
            st.info("La gráfica se generará tras el primer registro en la pestaña 'Utilidad'.")
    except Exception as e:
        st.error("Asegúrate de que la hoja 'Utilidad' tenga los encabezados correctos.")

# --- SIDEBAR: GESTIÓN ---
st.sidebar.header("🛠️ Panel Alaska")
if st.sidebar.button("🧹 LIMPIAR PANTALLA"):
    st.session_state.reset_key += 1
    st.rerun()

if st.sidebar.checkbox("🍔 Administrar Menú"):
    st.sidebar.subheader("Añadir")
    cat_a = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    nom_a = st.sidebar.text_input("Nombre")
    pre_a = st.sidebar.number_input("Precio Venta", min_value=0)
    cos_a = st.sidebar.number_input("Costo", min_value=0)
    if st.sidebar.button("Guardar Producto"):
        h_prod.append_row([cat_a, nom_a, pre_a, cos_a])
        if 'menu' in st.session_state: del st.session_state.menu
        st.rerun()
    
    st.sidebar.divider()
    st.sidebar.subheader("Borrar")
    cat_d = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"])
    if 'menu' in st.session_state:
        p_list = list(st.session_state.menu[cat_d].keys())
        if p_list:
            p_sel = st.sidebar.selectbox("Seleccione", p_list)
            if st.sidebar.button("Eliminar Producto"):
                celda = h_prod.find(p_sel)
                h_prod.delete_rows(celda.row)
                if 'menu' in st.session_state: del st.session_state.menu
                st.rerun()
