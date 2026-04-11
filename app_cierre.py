import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stNumberInput"] { width: 180px !important; }
    .resumen-footer { font-size: 16px; font-weight: bold; padding: 12px; border-radius: 8px; background-color: #1e2129; text-align: center; margin-top: 20px; }
    .dif-negativa { color: #ff4b4b; }
    .dif-positiva { color: #2ecc71; }
    .ganancia-card { background-color: #1e2129; padding: 20px; border-radius: 10px; border-left: 5px solid #2ecc71; }
    </style>
    """, unsafe_allow_html=True)

# 1. CONEXIÓN
def conectar_google():
    try:
        info_llave = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info_llave, scopes=scope)
        return gspread.authorize(creds).open("Base_Datos_Alaska")
    except: return None

doc = conectar_google()

# 2. CARGA DE DATOS
if doc:
    hoja_prod = doc.worksheet("Productos")
    hoja_cierre = doc.worksheet("Cierres")
    if 'menu' not in st.session_state:
        datos = hoja_prod.get_all_records()
        menu_temp = {"🍺 Bebidas": {}, "📦 Otros": {}}
        for fila in datos:
            p = float(fila.get('Precio', 0))
            c = float(fila.get('Costo', 0)) if fila.get('Costo') != "" else 0
            menu_temp[fila['Categoria']][fila['Producto']] = [p, c]
        st.session_state.menu = menu_temp

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# 3. PESTAÑAS
tab_bebidas, tab_comida, tab_otros, tab_arqueo, tab_ganancia = st.tabs(["🍺 Bebidas", "🍳 Comidas", "📦 Otros", "📉 ARQUEO", "💰 GANANCIA"])

v_esp = 0.0
c_tot = 0.0

with tab_bebidas:
    bus = st.text_input("🔍 Filtrar...", key=f"bus_{st.session_state.reset_key}").lower()
    for p, v in st.session_state.menu["🍺 Bebidas"].items():
        if bus in p.lower():
            st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"b_{p}_{st.session_state.reset_key}")
            cant = st.session_state.get(f"b_{p}_{st.session_state.reset_key}", 0)
            v_esp += (cant * v[0])
            c_tot += (cant * v[1])

with tab_comida:
    m_c = st.number_input("Comandas Cocina (₡)", min_value=0, step=1, key=f"c_{st.session_state.reset_key}")
    v_esp += m_c
    c_tot += (m_c * 0.6)

with tab_otros:
    for p, v in st.session_state.menu["📦 Otros"].items():
        st.number_input(f"{p} (₡{v[0]:,})", min_value=0, step=1, key=f"o_{p}_{st.session_state.reset_key}")
        cant = st.session_state.get(f"o_{p}_{st.session_state.reset_key}", 0)
        v_esp += (cant * v[0])
        c_tot += (cant * v[1])

with tab_arqueo:
    st.header("🧮 Arqueo")
    col_b, col_m = st.columns(2)
    t_efec = 0
    with col_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            t_efec += st.number_input(f"₡{b:,}", min_value=0, key=f"bil_{b}_{st.session_state.reset_key}") * b
    with col_m:
        for m in [500, 100, 50, 25, 10, 5]:
            t_efec += st.number_input(f"₡{m}", min_value=0, key=f"mon_{m}_{st.session_state.reset_key}") * m

    st.divider()
    sn = st.number_input("SINPE", min_value=0, key=f"sn_{st.session_state.reset_key}")
    tr = st.number_input("Tarjetas", min_value=0, key=f"tr_{st.session_state.reset_key}")
    pn = st.number_input("Pendientes", min_value=0, key=f"pn_{st.session_state.reset_key}")
    fd = st.number_input("Fondo Inicial", min_value=0, key=f"fd_{st.session_state.reset_key}")

    v_net = (t_efec + sn + tr + pn) - fd
    dif = v_net - v_esp

    c_dif = "dif-positiva" if dif >= 0 else "dif-negativa"
    st.markdown(f"""<div class="resumen-footer">Neta: ₡{v_net:,.0f} | Esp: ₡{v_esp:,.0f} | <span class="{c_dif}">Dif: ₡{dif:,.0f}</span></div>""", unsafe_allow_html=True)
    
    if st.button("💾 GUARDAR", use_container_width=True):
        gan = v_esp - c_tot
        hoja_cierre.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), v_esp, v_net, dif, gan])
        st.success("✅ ¡Guardado!")

with tab_ganancia:
    st.header("📊 Ganancias")
    gan_h = v_esp - c_tot
    st.markdown(f"<div class='ganancia-card'><h3>Ganancia de Hoy</h3><h1 style='color: #2ecc71;'>₡{gan_h:,.0f}</h1></div>", unsafe_allow_html=True)
    
    try:
        df = pd.DataFrame(hoja_cierre.get_all_records())
        if not df.empty and 'Ganancia' in df.columns:
            df['FechaDT'] = pd.to_datetime(df.iloc[:, 0], dayfirst=True)
            df['Mes'] = df['FechaDT'].dt.strftime('%Y-%m')
            resumen = df.groupby('Mes')['Ganancia'].sum().reset_index()
            st.bar_chart(data=resumen, x='Mes', y='Ganancia', color="#2ecc71")
    except:
        st.info("La gráfica aparecerá con datos limpios.")

# 4. SIDEBAR - RESTAURADO TOTALMENTE
st.sidebar.header("🧹 Acciones")
if st.sidebar.button("LIMPIAR CIERRE"):
    st.session_state.reset_key += 1
    st.rerun()

if st.sidebar.checkbox("⚙️ Configurar Menú"):
    st.sidebar.subheader("Añadir")
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
    st.sidebar.subheader("Eliminar")
    c_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"], key="dcat")
    if 'menu' in st.session_state:
        prods = list(st.session_state.menu[c_del].keys())
        if prods:
            p_del = st.sidebar.selectbox("Producto", prods, key="pdel_select")
            if st.sidebar.button("🗑️ Borrar"):
                celda = hoja_prod.find(p_del)
                hoja_prod.delete_rows(celda.row)
                if 'menu' in st.session_state: del st.session_state.menu
                st.rerun()
