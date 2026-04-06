import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

# CSS SOLO PARA LA PESTAÑA DE BEBIDAS (Para pegar las columnas y quitar espacios)
st.markdown("""
    <style>
    /* Forzar 2 columnas pegadas en móvil */
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 2px !important; /* Espacio mínimo entre columna 1 y 2 */
        }
        [data-testid="column"] {
            width: 50% !important;
            flex: 1 1 50% !important;
            min-width: 48% !important;
        }
        /* Quitar el espacio vacío interno del número para que se pegue al centro */
        div[data-testid="stNumberInput"] {
            width: 100% !important;
            margin-bottom: 0px !important;
        }
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

# --- 4. PESTAÑAS (Vuelven a su diseño original menos Bebidas) ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍳 Comidas", "📦 Otros", "📉 CIERRE"
])

ventas_esperadas = 0

# --- PESTAÑA BEBIDAS (Diseño de 2 columnas sin espacios vacíos) ---
with tab_bebidas:
    st.subheader("Selección de Bebidas")
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

# --- PESTAÑA COMIDAS (Original) ---
with tab_comida:
    st.subheader("Suma de Comandas")
    monto_comida = st.number_input("Total Ventas de Cocina (₡)", min_value=0, step=500, key="monto_total_comida")
    ventas_esperadas += monto_comida

# --- PESTAÑA OTROS (Original) ---
with tab_otros:
    st.subheader("Otros Productos")
    # Volvemos a lista simple para que no use el diseño de 2 columnas si no lo quieres aquí
    for prod, precio in st.session_state.menu["📦 Otros"].items():
        cant = st.number_input(f"{prod} (₡{precio:,})", min_value=0, key=f"otro_{prod}")
        ventas_esperadas += (cant * precio)

# --- PESTAÑA CIERRE FINAL (Original) ---
with tab_arqueo:
    st.header("🧮 Arqueo de Efectivo")
    col_b, col_m = st.columns(2)
    total_efectivo = 0
    with col_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            total_efectivo += st.number_input(f"₡{b:,}", min_value=0, step=1, key=f"billete_{b}") * b
    with col_m:
        for m in [500, 100, 50, 25, 10, 5]:
            total_efectivo += st.number_input(f"₡{m}", min_value=0, step=1, key=f"moneda_{m}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE Móvil", min_value=0, key="pago_sinpe")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, key="pago_tarjeta")
    pendientes = st.number_input("Pendientes (Fiados)", min_value=0, key="pago_pendientes")
    fondo = st.number_input("Fondo Inicial", min_value=0, key="caja_fondo")

    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales = total_reportado - fondo
    dif = ventas_reales - ventas_esperadas

    st.write(f"### Venta Neta: ₡{ventas_reales:,} | Esperada: ₡{ventas_esperadas:,}")
    
    if st.button("💾 GUARDAR CIERRE EN EXCEL", use_container_width=True):
        fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
        hoja_cierre.append_row([fecha_hoy, ventas_esperadas, total_reportado, dif])
        st.success("✅ Cierre guardado exitosamente.")

# --- SIDEBAR: GESTIÓN DE PRODUCTOS ---
st.sidebar.divider()
if st.sidebar.checkbox("⚙️ Configurar Menú"):
    st.sidebar.subheader("Añadir")
    cat_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    nom_add = st.sidebar.text_input("Nombre", key=f"input_nom_{st.session_state.reset_key}")
    pre_add = st.sidebar.number_input("Precio", min_value=0, key=f"input_pre_{st.session_state.reset_key}")
    
    if st.sidebar.button("➕ Guardar en Excel", use_container_width=True):
        if nom_add:
            hoja_prod.append_row([cat_add, nom_add, pre_add])
            st.session_state.reset_key += 1
            if 'menu' in st.session_state: del st.session_state.menu
            st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Eliminar")
    cat_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"])
    prods = list(st.session_state.menu[cat_del].keys())
    if prods:
        prod_del = st.sidebar.selectbox("Producto a borrar", prods)
        if st.sidebar.button("🗑️ Borrar de Excel", use_container_width=True):
            celda = hoja_prod.find(prod_del)
            hoja_prod.delete_rows(celda.row)
            if 'menu' in st.session_state: del st.session_state.menu
            st.rerun()
