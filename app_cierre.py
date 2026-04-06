import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA Y FORZADO AGRESIVO DE COLUMNAS ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

# Este bloque de CSS es el que obliga al celular a no amontonar todo
st.markdown("""
    <style>
    /* Forzar filas de 2 columnas en móvil */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
    }
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 45% !important;
    }
    /* Reducir espacio entre elementos para que quepan */
    .stNumberInput div div {
        padding: 0px !important;
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

st.title("💰 Gestión de Caja - Alaska")

# --- 4. PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍳 Comidas", "📦 Otros", "📉 CIERRE FINAL"
])

ventas_esperadas = 0

# --- PESTAÑA BEBIDAS (2 COLUMNAS FORZADAS) ---
with tab_bebidas:
    st.subheader("Selección de Bebidas")
    busqueda = st.text_input("🔍 Filtrar...", key="search_input").lower()
    
    lista_completa = list(st.session_state.menu["🍺 Bebidas"].items())
    lista_filtrada = [p for p in lista_completa if busqueda in p[0].lower()]
    
    for i in range(0, len(lista_filtrada), 2):
        # El contenedor horizontal ahora no se romperá en el móvil
        with st.container():
            c1, c2 = st.columns(2)
            p1, pre1 = lista_filtrada[i]
            with c1: 
                st.number_input(f"{p1}", min_value=0, step=1, key=f"bebida_{p1}", help=f"Precio: ₡{pre1:,}")
            
            if i + 1 < len(lista_filtrada):
                p2, pre2 = lista_filtrada[i+1]
                with c2: 
                    st.number_input(f"{p2}", min_value=0, step=1, key=f"bebida_{p2}", help=f"Precio: ₡{pre2:,}")

    total_bebidas = sum(st.session_state.get(f"bebida_{p}", 0) * pre for p, pre in lista_completa)
    ventas_esperadas += total_bebidas

# --- (El resto del código de comidas, otros y arqueo se mantiene igual) ---
# [Por brevedad mantengo la lógica pero asegúrate de no borrar las pestañas de abajo]
# ...

# --- BOTÓN GUARDAR CIERRE EN ARQUEO ---
# [Asegúrate de incluir el botón de guardar en la pestaña de Cierre Final]
