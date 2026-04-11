import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

# CSS - DISEÑO COMPACTO, BOTONES +/- VISIBLES Y RESUMEN DE COLORES
st.markdown("""
    <style>
    div[data-testid="stNumberInput"] { width: 180px !important; }
    .resumen-footer { 
        font-size: 16px; font-weight: bold; padding: 12px; 
        border-radius: 8px; background-color: #1e2129; 
        text-align: center; margin-top: 20px;
    }
    .dif-negativa { color: #ff4b4b; }
    .dif-positiva { color: #2ecc71; }
    .ganancia-card { background-color: #1e2129; padding: 20px; border-radius: 10px; border-left: 5px solid #2ecc71; }
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

# --- 2. CARGA DE DATOS ---
if doc:
    hoja_prod = doc.worksheet("Productos")
    hoja_cierre = doc.worksheet("Cierres")
    if 'menu' not in st.session_state:
        datos = hoja_prod.get_all_records()
        menu_temp = {"🍺 Bebidas": {}, "📦 Otros": {}}
        for fila in datos:
            precio = fila.get('Precio', 0)
            costo = fila.get('Costo', 0) if fila.get('Costo') != "" else 0
            menu_temp[fila['Categoria']][fila['Producto']] = [float(precio), float(costo)]
        st.session_state.menu = menu_temp

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 3. PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo, tab_ganancia = st.tabs([
    "🍺 Bebidas", "🍳 Comidas", "📦 Otros", "📉 ARQUEO", "💰 GANANCIA"
])

ventas_esperadas = 0.0
costos_totales = 0.0

# --- BEBIDAS ---
with tab_bebidas:
    st.subheader("Selección de Bebidas")
    busqueda = st.text_input("🔍 Filtrar...", key=f"bus_{st.session_state.reset_key}").lower()
    for p, v in st.session_state.menu["🍺 Bebidas"].items():
        if busqueda in p.lower():
            st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"b_{p}_{st.session_state.reset_key}")
            cant = st.session_state.get(f"b_{p}_{st.session_state.reset_key}", 0)
            ventas_esperadas += (cant * v[0])
            costos_totales += (cant * v[1])

# --- COMIDAS ---
with tab_comida:
    st.number_input("Monto Total Comandas (₡)", min_value=0, step=1, key=f"comida_{st.session_state.reset_key}")
    monto_c = st.session_state.get(f"comida_{st.session_state.reset_key}", 0)
    ventas_esperadas += monto_c
    costos_totales += (monto_c * 0.6)

# --- OTROS ---
with tab_otros:
    for p, v in st.session_state.menu["📦 Otros"].items():
        st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"o_{p}_{st.session_state.reset_key}")
        cant = st.session_state.get(f"o_{p}_{st.session_state.reset_key}", 0)
        ventas_esperadas += (cant * v[0])
        costos_totales += (cant * v[1])

# --- ARQUEO ---
with tab_arqueo:
    st.header("🧮 Arqueo")
    col_b, col_m = st.columns(2)
    t_efectivo = 0
    with col_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            t_efectivo += st.number_input(f"₡{b:,}", min_value=0, step=1, key=f"bil_{b}_{st.session_state.reset_key}") * b
    with col_m:
        for m in [500, 100, 50, 25, 10, 5]:
            t_efectivo += st.number_input(f"₡{m}", min_value=0, step=1, key=f"mon_{m}_{st.session_state.reset_key}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE", min_value=0, step=1, key=f"sinpe_{st.session_state.reset_key}")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, step=1, key=f"card_{st.session_state.reset_key}")
    pendientes = st.number_input("Pendientes", min_value=0, step=1, key=f"pend_{st.session_state.reset_key}")
    fondo = st.number_input("Fondo Inicial", min_value=0, step=1, key=f"fondo_{st.session_state.reset_key}")

    v_reales = (t_efectivo + sinpe + tarjetas + pendientes) - fondo
    dif = v_reales - ventas_esperadas

    color_dif = "dif-positiva" if dif >= 0 else "dif-negativa"
    st.markdown(f"""<div class="resumen-footer">Neta: ₡{v_reales:,.0f} | Esperada: ₡{ventas_esperadas:,.0f} | <span class="{color_dif}">Dif: ₡{dif:,.0f}</span></div>""", unsafe_allow_html=True)
    
    if st.button("💾 GUARDAR CIERRE", use_container_width=True):
        fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
        ganancia_dia = ventas_esperadas - costos_totales
        # ORDEN: Fecha, Esperada, Neta, Diferencia, Ganancia
        hoja_cierre.append_row([fecha_hoy, ventas_esperadas, v_reales, dif, ganancia_dia])
        st.success("✅ ¡Cierre guardado en el nuevo orden!")

# --- GANANCIA (GRÁFICA SEGURA) ---
with tab_ganancia:
    st.header("📊 Análisis")
    ganancia_hoy = ventas_esperadas - costos_totales
    st.markdown(f"<div class='ganancia-card'><h3>Ganancia de Hoy (Proyectada)</h3><h1 style='color: #2ecc71;'>₡{ganancia_hoy:,.0f}</h1></div>", unsafe_allow_html=True)
    
    try:
        df = pd.DataFrame(hoja_cierre.get_all_records())
        if not df.empty and 'Ganancia' in df.columns:
            df['FechaDT'] = pd.to_datetime(df.iloc[:, 0], dayfirst=True)
            df['Mes'] = df['FechaDT'].dt.strftime('%Y-%m')
            resumen = df.groupby('Mes')['Ganancia'].sum().reset_index()
            st.bar_chart(data=resumen, x='Mes', y='Ganancia', color="#2ecc71")
        else:
            st.info("La gráfica aparecerá cuando guardes cierres con la columna 'Ganancia'.")
    except:
        st.error("Error al cargar la gráfica. Revisa los encabezados de tu Excel.")

# --- SIDEBAR ---
st.sidebar.header("🧹 Acciones")
if st.sidebar.button("LIMPIAR CIERRE"):
    st.session_state.reset_key += 1
    st.rerun()

if st.sidebar.checkbox("⚙️ Configurar Menú"):
    c_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"], key="scat")
    n_add = st.sidebar.text_input("Nombre", key=f"nprod_{st.session_state.reset_key}")
    p_add = st.sidebar.number_input("Precio", min_value=0, key=f"pprod_{st.session_state.reset_key}")
    co_add = st.sidebar.number_input("Costo", min_value=0, key=f"cprod_{st.session_state.reset_key}")
    if st.sidebar.button("➕ Guardar"):
        if n_add:
            hoja_prod.append_row([c_add, n_add, p_add, co_add])
            if 'menu' in st.session_state: del st.session_state.menu
            st.rerun()
    st.sidebar.divider()
    if 'menu' in st.session_state:
        c_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"], key="dcat")
        prods = list(st.session_state.menu[c_del].keys())
        if prods:
            p_del = st.sidebar.selectbox("Producto", prods, key="pdel_select")
            if st.sidebar.button("🗑️ Borrar"):
                celda = hoja_prod.find(p_del)
                hoja_prod.delete_rows(celda.row)
                del st.session_state.menu
                st.rerun()
