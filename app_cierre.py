import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Alaska Control", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stNumberInput"] { width: 180px !important; }
    .resumen-footer { font-size: 16px; font-weight: bold; padding: 12px; border-radius: 8px; background-color: #1e2129; text-align: center; margin-top: 20px; }
    .dif-negativa { color: #ff4b4b; }
    .dif-positiva { color: #2ecc71; }
    .ganancia-card { background-color: #1e2129; padding: 20px; border-radius: 10px; border-left: 5px solid #2ecc71; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 1. CONEXIÓN A GOOGLE
def conectar():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                                                     scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open("Base_Datos_Alaska")
    except: return None

doc = conectar()

if doc:
    h_prod = doc.worksheet("Productos")
    h_cier = doc.worksheet("Cierres")
    if 'menu' not in st.session_state:
        datos = h_prod.get_all_records()
        menu_temp = {"🍺 Bebidas": {}, "📦 Otros": {}}
        for f in datos:
            cat = f.get('Categoria', '📦 Otros')
            menu_temp[cat][f['Producto']] = [float(f.get('Precio', 0)), float(f.get('Costo', 0))]
        st.session_state.menu = menu_temp

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# 2. INTERFAZ DE PESTAÑAS
t1, t2, t3, t4, t5 = st.tabs(["🍺 Bebidas", "🍳 Cocina", "📦 Otros", "📉 ARQUEO", "💰 GANANCIA"])

v_esperada = 0.0
c_materia_prima = 0.0

with t1:
    st.subheader("Bebidas")
    bus = st.text_input("🔍 Buscar...", key=f"bus_{st.session_state.reset_key}").lower()
    for p, v in st.session_state.menu["🍺 Bebidas"].items():
        if bus in p.lower():
            cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"b_{p}_{st.session_state.reset_key}")
            v_esperada += (cant * v[0])
            c_materia_prima += (cant * v[1])

with t2:
    st.subheader("Ventas de Cocina")
    m_cocina = st.number_input("Total Comandas (₡)", min_value=0, step=1, key=f"c_{st.session_state.reset_key}")
    v_esperada += m_cocina
    c_materia_prima += (m_cocina * 0.60) # Costo 60%

with t3:
    st.subheader("Otros Productos")
    for p, v in st.session_state.menu["📦 Otros"].items():
        cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"o_{p}_{st.session_state.reset_key}")
        v_esperada += (cant * v[0])
        c_materia_prima += (cant * v[1])

with t4:
    st.header("Arqueo de Caja")
    c1, c2 = st.columns(2)
    efectivo_total = 0
    with c1:
        for b in [20000, 10000, 5000, 2000, 1000]:
            efectivo_total += st.number_input(f"₡{b:,}", min_value=0, key=f"bil_{b}_{st.session_state.reset_key}") * b
    with c2:
        for m in [500, 100, 50, 25, 10, 5]:
            efectivo_total += st.number_input(f"₡{m}", min_value=0, key=f"mon_{m}_{st.session_state.reset_key}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE Móvil", min_value=0, key=f"sn_{st.session_state.reset_key}")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, key=f"tr_{st.session_state.reset_key}")
    pendientes = st.number_input("Pendientes (Fiados)", min_value=0, key=f"pn_{st.session_state.reset_key}")
    fondo = st.number_input("Fondo Inicial (Caja)", min_value=0, key=f"fd_{st.session_state.reset_key}")

    venta_neta_real = (efectivo_total + sinpe + tarjetas + pendientes) - fondo
    diferencia = venta_neta_real - v_esperada

    clase_dif = "dif-positiva" if diferencia >= 0 else "dif-negativa"
    st.markdown(f"""<div class="resumen-footer">Venta Neta: ₡{venta_neta_real:,.0f} | Diferencia: <span class="{clase_dif}">₡{diferencia:,.0f}</span></div>""", unsafe_allow_html=True)
    
    if st.button("💾 GUARDAR CIERRE", use_container_width=True):
        gan_bruta = v_esperada - c_materia_prima
        h_cier.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), v_esperada, venta_neta_real, diferencia, gan_bruta])
        st.success("✅ ¡Cierre guardado!")

with t5:
    st.header("Análisis de Utilidad")
    # CÁLCULO EN VIVO (Sin mirar el historial para evitar el millón negativo)
    utilidad_hoy = v_esperada - c_materia_prima
    
    st.markdown(f"""
    <div class='ganancia-card'>
        <p style='margin:0;'>Ganancia Bruta de lo Vendido (Hoy)</p>
        <h1 style='color: #2ecc71; margin:0;'>₡{utilidad_hoy:,.0f}</h1>
        <small>Venta Esperada (₡{v_esperada:,.0f}) - Costo Estimado (₡{c_materia_prima:,.0f})</small>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        registros = h_cier.get_all_records()
        if registros:
            df = pd.DataFrame(registros)
            if 'Ganancia' in df.columns:
                df['FechaDT'] = pd.to_datetime(df.iloc[:, 0], dayfirst=True)
                df['Mes'] = df['FechaDT'].dt.strftime('%Y-%m')
                resumen = df.groupby('Mes')['Ganancia'].sum().reset_index()
                st.subheader("Historial Mensual")
                st.bar_chart(data=resumen, x='Mes', y='Ganancia', color="#2ecc71")
        else: st.info("La gráfica aparecerá después del primer guardado.")
    except: st.error("Error al cargar gráfica.")

# SIDEBAR: GESTIÓN
st.sidebar.header("⚙️ Configuración")
if st.sidebar.button("🧹 LIMPIAR TODO"):
    st.session_state.reset_key += 1
    st.rerun()

if st.sidebar.checkbox("🍔 Editar Inventario"):
    st.sidebar.subheader("Agregar Producto")
    c_a = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    n_a = st.sidebar.text_input("Nombre")
    p_a = st.sidebar.number_input("Precio Venta", min_value=0)
    co_a = st.sidebar.number_input("Costo Materia Prima", min_value=0)
    if st.sidebar.button("Añadir"):
        h_prod.append_row([c_a, n_a, p_a, co_a])
        if 'menu' in st.session_state: del st.session_state.menu
        st.rerun()
    
    st.sidebar.divider()
    st.sidebar.subheader("Eliminar Producto")
    c_d = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"])
    if 'menu' in st.session_state:
        prods = list(st.session_state.menu[c_d].keys())
        if prods:
            p_d = st.sidebar.selectbox("Seleccione", prods)
            if st.sidebar.button("Eliminar"):
                celda = h_prod.find(p_d)
                h_prod.delete_rows(celda.row)
                if 'menu' in st.session_state: del st.session_state.menu
                st.rerun()
