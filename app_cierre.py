import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Alaska Control", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stNumberInput"] { width: 140px !important; }
    .resumen-footer { 
        font-size: 16px; font-weight: bold; padding: 12px; 
        border-radius: 8px; background-color: #1e2129; 
        text-align: center; margin-top: 20px; 
    }
    .dif-negativa { color: #ff4b4b; }
    .dif-positiva { color: #2ecc71; }
    </style>
    """, unsafe_allow_html=True)

# 1. CONEXIÓN
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

# 2. INTERFAZ
t1, t2, t3, t4 = st.tabs(["🍺 Bebidas", "🍳 Cocina", "📦 Otros", "📉 ARQUEO"])

v_esp = 0.0

with t1:
    st.subheader("Bebidas")
    bus = st.text_input("🔍 Buscar...", key=f"bus_{st.session_state.reset_key}").lower()
    for p, v in st.session_state.menu["🍺 Bebidas"].items():
        if bus in p.lower():
            cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"b_{p}_{st.session_state.reset_key}")
            v_esp += (cant * v[0])

with t2:
    st.subheader("Ventas Cocina")
    m_c = st.number_input("Total Comandas (₡)", min_value=0, step=1, key=f"c_{st.session_state.reset_key}")
    v_esp += m_c

with t3:
    st.subheader("Otros")
    for p, v in st.session_state.menu["📦 Otros"].items():
        cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"o_{p}_{st.session_state.reset_key}")
        v_esp += (cant * v[0])

with t4:
    st.header("Arqueo de Caja")
    c1, c2 = st.columns(2)
    t_efec = 0
    with c1:
        for b in [20000, 10000, 5000, 2000, 1000]:
            t_efec += st.number_input(f"₡{b:,}", min_value=0, key=f"bil_{b}_{st.session_state.reset_key}") * b
    with c2:
        for m in [500, 100, 50, ]:
            t_efec += st.number_input(f"₡{m}", min_value=0, key=f"mon_{m}_{st.session_state.reset_key}") * m

    st.divider()
    sn = st.number_input("Total SINPE", min_value=0, key=f"sn_{st.session_state.reset_key}")
    tr = st.number_input("Total Tarjetas", min_value=0, key=f"tr_{st.session_state.reset_key}")
    pn = st.number_input("Pendientes (Fiados)", min_value=0, key=f"pn_{st.session_state.reset_key}")
    fd = st.number_input("Fondo Inicial", min_value=0, key=f"fd_{st.session_state.reset_key}")

    v_neta = (t_efec + sn + tr + pn) - fd
    dif = v_neta - v_esp

    color = "dif-positiva" if dif >= 0 else "dif-negativa"
    st.markdown(f"""<div class="resumen-footer">Venta Neta: ₡{v_neta:,.0f} | Diferencia: <span class="{color}">₡{dif:,.0f}</span></div>""", unsafe_allow_html=True)
    
    if st.button("💾 GUARDAR CIERRE", use_container_width=True):
        # Guardamos solo datos básicos: Fecha, Esperada, Neta, Diferencia
        h_cier.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), v_esp, v_neta, dif])
        st.success("✅ ¡Cierre guardado!")

# SIDEBAR
st.sidebar.header("⚙️ Configuración")
if st.sidebar.button("🧹 LIMPIAR TODO"):
    st.session_state.reset_key += 1
    st.rerun()

if st.sidebar.checkbox("🍔 Editar Productos"):
    st.sidebar.subheader("Agregar")
    ca = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    na = st.sidebar.text_input("Nombre")
    pa = st.sidebar.number_input("Precio", min_value=0)
    co = st.sidebar.number_input("Costo", min_value=0)
    if st.sidebar.button("Añadir"):
        h_prod.append_row([ca, na, pa, co])
        if 'menu' in st.session_state: del st.session_state.menu
        st.rerun()
    
    st.sidebar.divider()
    st.sidebar.subheader("Eliminar")
    cd = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"])
    if 'menu' in st.session_state:
        prods = list(st.session_state.menu[cd].keys())
        if prods:
            pd = st.sidebar.selectbox("Seleccione", prods)
            if st.sidebar.button("Borrar"):
                c = h_prod.find(pd)
                h_prod.delete_rows(c.row)
                if 'menu' in st.session_state: del st.session_state.menu
                st.rerun()
