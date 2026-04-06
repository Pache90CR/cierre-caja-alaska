import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA Y DISEÑO PARA MÓVIL ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

st.markdown("""
    <style>
    /* 1. Forzar 2 columnas en móvil sin que se amontonen */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
    }
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 48% !important;
    }
    /* 2. Ajustar el ancho del selector de número para que no sobre espacio */
    div[data-testid="stNumberInput"] {
        width: 100% !important;
    }
    /* 3. Hacer los botones +/- y el cuadro de texto más compactos */
    div[data-testid="stNumberInput"] div div {
        gap: 2px !important;
    }
    input {
        padding: 2px !important;
    }
    /* 4. Etiquetas más pequeñas para que no empujen el diseño */
    label {
        font-size: 13px !important;
        white-space: nowrap !important;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
def conectar_google():
    try:
        info_llave = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info_llave, scopes=scope)
        cliente = gspread.authorize(creds)
        return cliente.open("Base_Datos_Alaska")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

doc = conectar_google()

# --- 2. GESTIÓN DE DATOS ---
if doc:
    hoja_prod = doc.worksheet("Productos")
    hoja_cierre = doc.worksheet("Cierres")

    if 'menu' not in st.session_state:
        datos = hoja_prod.get_all_records()
        menu_temp = {"🍺 Bebidas": {}, "📦 Otros": {}}
        for fila in datos:
            menu_temp[fila['Categoria']][fila['Producto']] = fila['Precio']
        st.session_state.menu = menu_temp

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

# --- 3. FUNCIONES ---
def limpiar_cierre():
    for key in list(st.session_state.keys()):
        if key.startswith(('bebida_', 'otro_', 'billete_', 'moneda_', 'pago_', 'monto_total_comida')):
            st.session_state[key] = 0
    st.toast("✅ Campos reiniciados", icon="🧹")

st.title("💰 Gestión Alaska")

# Botón Limpiar en Sidebar
st.sidebar.header("🧹 Acciones")
if st.sidebar.button("LIMPIAR TODO EL CIERRE", use_container_width=True, type="primary"):
    limpiar_cierre()
    st.rerun()

# --- 4. PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍳 Comidas", "📦 Otros", "📉 CIERRE"
])

ventas_esperadas = 0

# --- PESTAÑA BEBIDAS ---
with tab_bebidas:
    busqueda = st.text_input("🔍 Filtrar...", key="search_input").lower()
    lista_completa = list(st.session_state.menu["🍺 Bebidas"].items())
    lista_filtrada = [p for p in lista_completa if busqueda in p[0].lower()]
    
    for i in range(0, len(lista_filtrada), 2):
        c1, c2 = st.columns(2)
        p1, pre1 = lista_filtrada[i]
        with c1: 
            st.number_input(f"{p1}", min_value=0, step=1, key=f"bebida_{p1}")
        
        if i + 1 < len(lista_filtrada):
            p2, pre2 = lista_filtrada[i+1]
            with c2: 
                st.number_input(f"{p2}", min_value=0, step=1, key=f"bebida_{p2}")

    total_bebidas = sum(st.session_state.get(f"bebida_{p}", 0) * pre for p, pre in lista_completa)
    ventas_esperadas += total_bebidas

# --- PESTAÑA COMIDA ---
with tab_comida:
    monto_comida = st.number_input("Total Comandas Cocina (₡)", min_value=0, step=500, key="monto_total_comida")
    ventas_esperadas += monto_comida

# --- PESTAÑA OTROS ---
with tab_otros:
    lista_otros = list(st.session_state.menu["📦 Otros"].items())
    for i in range(0, len(lista_otros), 2):
        c1, c2 = st.columns(2)
        p1, pre1 = lista_otros[i]
        with c1: st.number_input(f"{p1}", min_value=0, step=1, key=f"otro_{p1}")
        if i + 1 < len(lista_otros):
            p2, pre2 = lista_otros[i+1]
            with c2: st.number_input(f"{p2}", min_value=0, step=1, key=f"otro_{p2}")
    
    total_otros = sum(st.session_state.get(f"otro_{p}", 0) * pre for p, pre in lista_otros)
    ventas_esperadas += total_otros

# --- PESTAÑA CIERRE FINAL ---
with tab_arqueo:
    st.header("🧮 Arqueo")
    col_b, col_m = st.columns(2)
    total_efectivo = 0
    with col_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            total_efectivo += st.number_input(f"₡{b:,}", min_value=0, step=1, key=f"billete_{b}") * b
    with col_m:
        for m in [500, 100, 50, 25, 10, 5]:
            total_efectivo += st.number_input(f"₡{m}", min_value=0, step=1, key=f"moneda_{m}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE", min_value=0, key="pago_sinpe")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, key="pago_tarjeta")
    pendientes = st.number_input("Pendientes (Fiados)", min_value=0, key="pago_pendientes")
    fondo = st.number_input("Fondo Inicial", min_value=0, key="caja_fondo")

    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales = total_reportado - fondo
    dif = ventas_reales - ventas_esperadas

    st.write(f"### Venta Neta: ₡{ventas_reales:,}")
    st.write(f"### Esperada: ₡{ventas_esperadas:,}")
    
    if st.button("💾 GUARDAR CIERRE EN EXCEL", use_container_width=True):
        fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
        hoja_cierre.append_row([fecha_hoy, ventas_esperadas, total_reportado, dif])
        st.success("✅ ¡Cierre guardado!")

# --- SIDEBAR: GESTIÓN PRODUCTOS ---
st.sidebar.divider()
if st.sidebar.checkbox("⚙️ Configurar Menú"):
    cat_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"], key="sidebar_cat_add")
    nom_add = st.sidebar.text_input("Nombre", key=f"input_nom_{st.session_state.reset_key}")
    pre_add = st.sidebar.number_input("Precio", min_value=0, key=f"input_pre_{st.session_state.reset_key}")
    if st.sidebar.button("➕ Guardar", use_container_width=True):
        if nom_add:
            hoja_prod.append_row([cat_add, nom_add, pre_add])
            st.session_state.reset_key += 1
            if 'menu' in st.session_state: del st.session_state.menu
            st.rerun()

    st.sidebar.divider()
    cat_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"], key="sidebar_cat_del")
    prods = list(st.session_state.menu[cat_del].keys())
    if prods:
        prod_del = st.sidebar.selectbox("Borrar producto", prods)
        if st.sidebar.button("🗑️ Borrar", use_container_width=True):
            try:
                celda = hoja_prod.find(prod_del)
                hoja_prod.delete_rows(celda.row)
                if 'menu' in st.session_state: del st.session_state.menu
                st.rerun()
            except:
                st.sidebar.error("Error al borrar")

