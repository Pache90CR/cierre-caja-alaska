import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Cierre Alaska", layout="centered")

# --- CSS COMPACTO (El que te gustó) ---
st.markdown("""
    <style>
    @media (max-width: 640px) {
        div[data-testid="column"] { padding: 0px 1px !important; margin: 0px !important; }
        div[data-testid="stHorizontalBlock"] { gap: 0px !important; }
    }
    div[data-testid="stNumberInput"] div { margin: 0px auto !important; padding: 0px !important; max-width: 140px !important; }
    [data-testid="stMarkdown"] p { font-size: 13px !important; white-space: nowrap !important; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px !important; }
    .ganancia-text { color: #2ecc71; font-weight: bold; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. CONEXIÓN ---
def conectar_google():
    try:
        info_llave = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info_llave, scopes=scope)
        return gspread.authorize(creds).open("Base_Datos_Alaska")
    except: return None

doc = conectar_google()

# --- 2. GESTIÓN DE DATOS (Incluye Costos) ---
if doc:
    hoja_prod = doc.worksheet("Productos")
    hoja_cierre = doc.worksheet("Cierres")
    if 'menu' not in st.session_state:
        datos = hoja_prod.get_all_records()
        menu_temp = {"🍺 Bebidas": {}, "📦 Otros": {}}
        for fila in datos:
            # Guardamos [Precio, Costo]
            menu_temp[fila['Categoria']][fila['Producto']] = [fila['Precio'], fila.get('Costo', 0)]
        st.session_state.menu = menu_temp

# --- 3. PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs(["🍺 Bebidas", "🍳 Comidas", "📦 Otros", "📉 CIERRE"])

ventas_esperadas = 0
costos_totales = 0

# PESTAÑA BEBIDAS
with tab_bebidas:
    busqueda = st.text_input("🔍 Filtrar...", key="search_input").lower()
    lista_completa = list(st.session_state.menu["🍺 Bebidas"].items())
    lista_filtrada = [p for p in lista_completa if busqueda in p[0].lower()]
    
    for i in range(0, len(lista_filtrada), 2):
        c1, c2 = st.columns(2)
        p1, valores1 = lista_filtrada[i]
        with c1: st.number_input(f"{p1}", min_value=0, step=1, key=f"bebida_{p1}")
        if i + 1 < len(lista_filtrada):
            p2, valores2 = lista_filtrada[i+1]
            with c2: st.number_input(f"{p2}", min_value=0, step=1, key=f"bebida_{p2}")

    # Cálculo de Venta y Ganancia
    total_beb_venta = sum(st.session_state.get(f"bebida_{p}", 0) * val[0] for p, val in lista_completa)
    total_beb_costo = sum(st.session_state.get(f"bebida_{p}", 0) * val[1] for p, val in lista_completa)
    ventas_esperadas += total_beb_venta
    costos_totales += total_beb_costo

# PESTAÑA COMIDAS
with tab_comida:
    monto_comida = st.number_input("Total Comandas Cocina (₡)", min_value=0, step=500, key="monto_total_comida")
    ventas_esperadas += monto_comida
    # Estimamos que el costo de comida es el 60% (Ganancia 40%)
    costos_totales += (monto_comida * 0.6)

# PESTAÑA OTROS (Similar a bebidas)
with tab_otros:
    lista_o = list(st.session_state.menu["📦 Otros"].items())
    for p, val in lista_o:
        cant = st.number_input(f"{p}", min_value=0, key=f"otro_{p}")
        ventas_esperadas += (cant * val[0])
        costos_totales += (cant * val[1])

# PESTAÑA CIERRE FINAL
with tab_arqueo:
    st.header("🧮 Arqueo")
    # ... (Lógica de billetes y monedas que ya tienes) ...
    # Supongamos que ya calculamos total_reportado y diferencia
    
    ganancia_neta = ventas_esperadas - costos_totales
    
    st.divider()
    st.write(f"### Venta Esperada: ₡{ventas_esperadas:,}")
    st.markdown(f"### Ganancia Estimada: <span class='ganancia-text'>₡{ganancia_neta:,}</span>", unsafe_allow_html=True)
    st.info(f"Margen de utilidad: {round((ganancia_neta/ventas_esperadas)*100 if ventas_esperadas > 0 else 0, 1)}%")

    if st.button("💾 GUARDAR CIERRE Y GANANCIAS", use_container_width=True):
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        # Guardamos la ganancia en una nueva columna en Excel
        # Asegúrate que tu pestaña "Cierres" tenga una columna para 'Ganancia'
        hoja_cierre.append_row([fecha, ventas_esperadas, ganancia_neta, "Caja OK"])
        st.success("✅ Cierre y Ganancias guardadas.")
