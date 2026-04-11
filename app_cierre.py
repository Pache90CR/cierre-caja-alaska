import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

# CSS - COMPACTO PERO CON BOTONES VISIBLES
st.markdown("""
    <style>
    /* Ajuste para que el cuadro sea compacto pero muestre los botones +/- */
    div[data-testid="stNumberInput"] {
        width: 150px !important;
    }
    /* Estilo del resumen de arqueo */
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

# --- 2. DATOS ---
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
    busqueda = st.text_input("🔍 Filtrar...", key="search_input").lower()
    for p, v in st.session_state.menu["🍺 Bebidas"].items():
        if busqueda in p.lower():
            st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"bebida_{p}")
            ventas_esperadas += (st.session_state.get(f"bebida_{p}", 0) * v[0])
            costos_totales += (st.session_state.get(f"bebida_{p}", 0) * v[1])

# --- COMIDAS ---
with tab_comida:
    monto_comida = st.number_input("Total Comandas Cocina (₡)", min_value=0, step=500, key="monto_total_comida")
    ventas_esperadas += monto_comida
    costos_totales += (monto_comida * 0.6)

# --- OTROS ---
with tab_otros:
    for p, v in st.session_state.menu["📦 Otros"].items():
        st.number_input(f"{p} (₡{v[0]:,})", min_value=0, key=f"otro_{p}")
        ventas_esperadas += (st.session_state.get(f"otro_{p}", 0) * v[0])
        costos_totales += (st.session_state.get(f"otro_{p}", 0) * v[1])

# --- ARQUEO ---
with tab_arqueo:
    st.header("🧮 Arqueo")
    col_b, col_m = st.columns(2)
    total_efectivo = 0
    with col_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            total_efectivo += st.number_input(f"₡{b:,}", min_value=0, key=f"billete_{b}") * b
    with col_m:
        for m in [500, 100, 50, 25, 10, 5]:
            total_efectivo += st.number_input(f"₡{m}", min_value=0, key=f"moneda_{m}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE", min_value=0, key="pago_sinpe")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, key="pago_tarjeta")
    pendientes = st.number_input("Pendientes", min_value=0, key="pago_pendientes")
    fondo = st.number_input("Fondo Inicial", min_value=0, key="caja_fondo")

    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales = total_reportado - fondo
    dif = ventas_reales - ventas_esperadas

    color_dif = "dif-positiva" if dif >= 0 else "dif-negativa"
    st.markdown(f"""<div class="resumen-footer">Neta: ₡{ventas_reales:,.0f} | Esperada: ₡{ventas_esperadas:,.0f} | <span class="{color_dif}">Dif: ₡{dif:,.0f}</span></div>""", unsafe_allow_html=True)
    
    if st.button("💾 GUARDAR CIERRE", use_container_width=True):
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        ganancia_dia = ventas_reales - costos_totales
        hoja_cierre.append_row([fecha, ventas_reales, ganancia_dia, dif])
        st.success("✅ ¡Guardado!")

# --- GANANCIA ---
with tab_ganancia:
    st.header("📊 Análisis")
    ganancia_ahora = ventas_esperadas - costos_totales
    st.markdown(f"<div class='ganancia-card'><h3>Ganancia de Hoy</h3><h1 style='color: #2ecc71;'>₡{ganancia_ahora:,.0f}</h1></div>", unsafe_allow_html=True)
    
    try:
        registros = hoja_cierre.get_all_records()
        if registros:
            df = pd.DataFrame(registros)
            # Forzamos que la primera columna sea fecha y la tercera ganancia
            df['FechaDT'] = pd.to_datetime(df.iloc[:, 0], dayfirst=True)
            df['Mes'] = df['FechaDT'].dt.strftime('%Y-%m')
            resumen = df.groupby('Mes').iloc[:, 2].sum().reset_index()
            st.bar_chart(data=resumen, x='Mes', y=resumen.columns[1], color="#2ecc71")
    except:
        st.info("Gráfica disponible tras guardar cierres.")

# --- SIDEBAR (RESTAURADO ELIMINAR) ---
st.sidebar.header("🧹 Acciones")
if st.sidebar.button("LIMPIAR CIERRE"):
    for key in list(st.session_state.keys()):
        if key.startswith(('bebida_', 'otro_', 'billete_', 'moneda_', 'pago_', 'monto_total_comida')):
            st.session_state[key] = 0
    st.rerun()

if st.sidebar.checkbox("⚙️ Configurar Menú"):
    st.sidebar.subheader("Añadir")
    cat_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"], key="s_cat")
    nom_add = st.sidebar.text_input("Nombre", key=f"n_{st.session_state.reset_key}")
    pre_add = st.sidebar.number_input("Precio", min_value=0, key=f"p_{st.session_state.reset_key}")
    cos_add = st.sidebar.number_input("Costo", min_value=0, key=f"c_{st.session_state.reset_key}")
    if st.sidebar.button("➕ Guardar"):
        hoja_prod.append_row([cat_add, nom_add, pre_add, cos_add])
        st.session_state.reset_key += 1
        del st.session_state.menu
        st.rerun()
    
    st.sidebar.divider()
    st.sidebar.subheader("Eliminar")
    cat_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"], key="d_cat")
    if 'menu' in st.session_state:
        prods = list(st.session_state.menu[cat_del].keys())
        if prods:
            prod_del = st.sidebar.selectbox("Producto", prods)
            if st.sidebar.button("🗑️ Borrar"):
                celda = hoja_prod.find(prod_del)
                hoja_prod.delete_rows(celda.row)
                del st.session_state.menu
                st.rerun()



