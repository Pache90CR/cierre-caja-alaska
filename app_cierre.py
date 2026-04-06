import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

# --- CSS MAESTRO PARA FORZAR 2 COLUMNAS ---
st.markdown("""
    <style>
    /* Forzar que el contenedor de las columnas NO se rompa */
    div[data-testid="column"] {
        width: 49% !important;
        flex: 1 1 49% !important;
        min-width: 45% !important;
        margin: 0px !important;
        padding: 5px !important;
    }
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* Prohíbe que la segunda columna baje */
        gap: 2px !important;
    }
    /* Compactar el input de número para que no estire la columna */
    div[data-testid="stNumberInput"] {
        width: 100% !important;
    }
    div[data-testid="stNumberInput"] div div {
        gap: 1px !important;
    }
    input {
        padding: 5px !important;
        text-align: center !important;
    }
    /* Etiquetas pequeñas para ganar espacio */
    label p {
        font-size: 14px !important;
        white-space: nowrap !important;
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
        st.error("Error de conexión con Google Sheets")
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
    st.toast("✅ Cierre reiniciado", icon="🧹")

st.title("💰 Gestión Alaska")

# --- 4. PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍳 Comidas", "📦 Otros", "📉 CIERRE"
])

ventas_esperadas = 0

# --- PESTAÑA BEBIDAS (DISEÑO 2 COLUMNAS FORZADO) ---
with tab_bebidas:
    st.subheader("Selección de Bebidas")
    busqueda = st.text_input("🔍 Filtrar...", key="search_input").lower()
    
    lista_completa = list(st.session_state.menu["🍺 Bebidas"].items())
    lista_filtrada = [p for p in lista_completa if busqueda in p[0].lower()]
    
    # El truco está aquí: generamos filas de 2 columnas con CSS inyectado
    for i in range(0, len(lista_filtrada), 2):
        col1, col2 = st.columns(2)
        
        # Producto 1
        p1, pre1 = lista_filtrada[i]
        with col1:
            st.number_input(p1, min_value=0, step=1, key=f"bebida_{p1}")
        
        # Producto 2
        if i + 1 < len(lista_filtrada):
            p2, pre2 = lista_filtrada[i+1]
            with col2:
                st.number_input(p2, min_value=0, step=1, key=f"bebida_{p2}")

    total_bebidas = sum(st.session_state.get(f"bebida_{p}", 0) * pre for p, pre in lista_completa)
    ventas_esperadas += total_bebidas

# --- PESTAÑA COMIDAS (Standard) ---
with tab_comida:
    monto_comida = st.number_input("Total Comandas Cocina (₡)", min_value=0, step=500, key="monto_total_comida")
    ventas_esperadas += monto_comida

# --- PESTAÑA OTROS (Standard) ---
with tab_otros:
    for prod, precio in st.session_state.menu["📦 Otros"].items():
        cant = st.number_input(f"{prod} (₡{precio:,})", min_value=0, key=f"otro_{prod}")
        ventas_esperadas += (cant * precio)

# --- PESTAÑA CIERRE FINAL ---
with tab_arqueo:
    st.header("🧮 Arqueo")
    total_efectivo = 0
    c_b, c_m = st.columns(2)
    with c_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            total_efectivo += st.number_input(f"₡{b:,}", min_value=0, key=f"billete_{b}") * b
    with c_m:
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

    st.write(f"### Venta Neta: ₡{ventas_reales:,} | Esperada: ₡{ventas_esperadas:,}")
    if st.button("💾 GUARDAR EN EXCEL", use_container_width=True):
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        hoja_cierre.append_row([fecha, ventas_esperadas, total_reportado, dif])
        st.success("✅ Cierre guardado")

# --- SIDEBAR (LIMPIAR Y GESTIÓN) ---
st.sidebar.header("🧹 Acciones")
if st.sidebar.button("LIMPIAR TODO"):
    limpiar_cierre()
    st.rerun()

if st.sidebar.checkbox("⚙️ Configurar Menú"):
    cat = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    nom = st.sidebar.text_input("Nombre", key=f"in_{st.session_state.reset_key}")
    pre = st.sidebar.number_input("Precio", min_value=0, key=f"ip_{st.session_state.reset_key}")
    if st.sidebar.button("➕ Guardar"):
        hoja_prod.append_row([cat, nom, pre])
        st.session_state.reset_key += 1
        del st.session_state.menu
        st.rerun()


