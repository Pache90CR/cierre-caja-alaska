import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

# CSS - DISEÑO COMPACTO CON BOTONES VISIBLES (COMO TE GUSTA)
st.markdown("""
    <style>
    /* Ajuste para que el cuadro sea compacto pero muestre los botones +/- */
    div[data-testid="stNumberInput"] {
        width: 180px !important;
    }
    /* Estilo del resumen de arqueo con colores */
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

# Inicializar reset_key para limpieza segura
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

# --- 3. PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo, tab_ganancia = st.tabs([
    "🍺 Bebidas", "🍳 Comidas", "📦 Otros", "📉 ARQUEO", "💰 GANANCIA"
])

ventas_esperadas = 0.0
costos_totales = 0.0

# --- BEBIDAS ---
with tab_bebidas:
    st.subheader("Selección de Bebidas")
    busqueda = st.text_input("🔍 Filtrar...", key=f"search_{st.session_state.reset_key}").lower()
    for p, v in st.session_state.menu["🍺 Bebidas"].items():
        if busqueda in p.lower():
            # Usamos el reset_key en la llave para que se limpie de verdad sin errores
            st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"bebida_{p}_{st.session_state.reset_key}")
            cant = st.session_state.get(f"bebida_{p}_{st.session_state.reset_key}", 0)
            ventas_esperadas += (cant * v[0])
            costos_totales += (cant * v[1])

# --- COMIDAS ---
with tab_comida:
    st.subheader("Ventas de Cocina")
    st.number_input("Monto Total Comandas (₡)", min_value=0, step=1, key=f"monto_total_comida_{st.session_state.reset_key}")
    monto_c = st.session_state.get(f"monto_total_comida_{st.session_state.reset_key}", 0)
    ventas_esperadas += monto_c
    costos_totales += (monto_c * 0.6)

# --- OTROS ---
with tab_otros:
    for p, v in st.session_state.menu["📦 Otros"].items():
        st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"otro_{p}_{st.session_state.reset_key}")
        cant = st.session_state.get(f"otro_{p}_{st.session_state.reset_key}", 0)
        ventas_esperadas += (cant * v[0])
        costos_totales += (cant * v[1])

# --- ARQUEO ---
with tab_arqueo:
    st.header("🧮 Arqueo")
    col_b, col_m = st.columns(2)
    t_efectivo = 0
    with col_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            t_efectivo += st.number_input(f"₡{b:,}", min_value=0, step=1, key=f"billete_{b}_{st.session_state.reset_key}") * b
    with col_m:
        for m in [500, 100, 50, 25, 10, 5]:
            t_efectivo += st.number_input(f"₡{m}", min_value=0, step=1, key=f"moneda_{m}_{st.session_state.reset_key}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE", min_value=0, step=1, key=f"pago_sinpe_{st.session_state.reset_key}")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, step=1, key=f"pago_tarjeta_{st.session_state.reset_key}")
    pendientes = st.number_input("Pendientes", min_value=0, step=1, key=f"pago_pendientes_{st.session_state.reset_key}")
    fondo = st.number_input("Fondo Inicial", min_value=0, step=1, key=f"caja_fondo_{st.session_state.reset_key}")

    v_reales = (t_efectivo + sinpe + tarjetas + pendientes) - fondo
    dif = v_reales - ventas_esperadas

    color_dif = "dif-positiva" if dif >= 0 else "dif-negativa"
    st.markdown(f"""<div class="resumen-footer">Neta: ₡{v_reales:,.0f} | Esperada: ₡{ventas_esperadas:,.0f} | <span class="{color_dif}">Dif: ₡{dif:,.0f}</span></div>""", unsafe_allow_html=True)
    
    if st.button("💾 GUARDAR CIERRE", use_container_width=True):
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        ganancia_dia = v_reales - costos_totales
        hoja_cierre.append_row([fecha, v_reales, ganancia_dia, dif])
        st.success("✅ ¡Guardado!")

# --- GANANCIA ---
with tab_ganancia:
    st.header("📊 Análisis")
    ganancia_ahora = ventas_esperadas - costos_totales
    st.markdown(f"<div class='ganancia-card'><h3>Utilidad de Hoy</h3><h1 style='color: #2ecc71;'>₡{ganancia_ahora:,.0f}</h1></div>", unsafe_allow_html=True)
    
    try:
        registros = hoja_cierre.get_all_records()
        if registros:
            df = pd.DataFrame(registros)
            df['FechaDT'] = pd.to_datetime(df.iloc[:, 0], dayfirst=True)
            df['Mes'] = df['FechaDT'].dt.strftime('%Y-%m')
            resumen = df.groupby('Mes').agg({df.columns[2]: 'sum'}).reset_index()
            st.bar_chart(data=resumen, x='Mes', y=resumen.columns[1], color="#2ecc71")
    except:
        st.info("Gráfica disponible tras guardar cierres.")

# --- SIDEBAR (GESTIÓN) ---
st.sidebar.header("🧹 Acciones")
# BOTÓN DE LIMPIEZA TOTALMENTE SEGURO
if st.sidebar.button("LIMPIAR CIERRE"):
    # En lugar de borrar uno por uno, cambiamos la 'reset_key'
    # Esto obliga a Streamlit a renderizar widgets nuevos y limpios
    st.session_state.reset_key += 1
    st.rerun()

if st.sidebar.checkbox("⚙️ Configurar Menú"):
    st.sidebar.subheader("Añadir")
    c_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"], key="s_cat")
    n_add = st.sidebar.text_input("Nombre", key=f"new_prod_name_{st.session_state.reset_key}")
    p_add = st.sidebar.number_input("Precio", min_value=0, key=f"new_prod_price_{st.session_state.reset_key}")
    co_add = st.sidebar.number_input("Costo", min_value=0, key=f"new_prod_cost_{st.session_state.reset_key}")
    if st.sidebar.button("➕ Guardar"):
        if n_add:
            hoja_prod.append_row([c_add, n_add, p_add, co_add])
            del st.session_state.menu
            st.rerun()
    
    st.sidebar.divider()
    st.sidebar.subheader("Eliminar")
    c_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"], key="d_cat")
    if 'menu' in st.session_state:
        prods = list(st.session_state.menu[c_del].keys())
        if prods:
            p_del = st.sidebar.selectbox("Producto", prods)
            if st.sidebar.button("🗑️ Borrar"):
                celda = hoja_prod.find(p_del)
                hoja_prod.delete_rows(celda.row)
                del st.session_state.menu
                st.rerun()





