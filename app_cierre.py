import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

# CSS AGRESIVO PARA ELIMINAR ESPACIOS (FORZADO MÓVIL)
# Solo afecta a las Bebidas y Otros si los usas en 2 columnas
st.markdown("""
    <style>
    /* 1. Unir las dos columnas al centro del celular */
    @media (max-width: 640px) {
        div[data-testid="column"] {
            padding: 0px 1px !important; /* Espacio mínimo lateral de cada columna */
            margin: 0px !important;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 0px !important; /* Espacio CERO entre columna 1 y columna 2 */
        }
    }

    /* 2. Compactar el selector de número (Eliminar los "espacios vacíos" rojos) */
    div[data-testid="stNumberInput"] div {
        margin: 0px auto !important; /* Centra el input y quita márgenes */
        padding: 0px !important;
        max-width: 140px !important; /* Limita el ancho para que no se estire */
    }
    
    /* 3. Ajustar el ancho del texto del producto para que no empuje el diseño */
    [data-testid="stMarkdown"] p {
        font-size: 13px !important;
        white-space: nowrap !important;
        overflow: hidden;
        text-overflow: ellipsis; /* Pone ... si el nombre es muy largo */
        margin-bottom: 2px !important;
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
        # Cargar productos desde Google Sheets
        datos = hoja_prod.get_all_records()
        menu_temp = {"🍺 Bebidas": {}, "📦 Otros": {}}
        for fila in datos:
            menu_temp[fila['Categoria']][fila['Producto']] = fila['Precio']
        st.session_state.menu = menu_temp

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

# --- 3. FUNCIONES ---
def limpiar_cierre():
    # Recorrer llaves y poner montos en 0
    for key in list(st.session_state.keys()):
        if key.startswith(('bebida_', 'otro_', 'billete_', 'moneda_', 'pago_', 'monto_total_comida')):
            st.session_state[key] = 0
    st.toast("✅ Campos reiniciados", icon="🧹")

st.title("💰 Gestión de Caja - Alaska")

# --- 4. PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍳 Ventas Comida", "📦 Otros", "📉 CIERRE FINAL"
])

ventas_esperadas = 0

# --- PESTAÑA BEBIDAS (AQUÍ ESTÁ EL DISEÑO FORZADO) ---
with tab_bebidas:
    st.subheader("Selección de Bebidas")
    busqueda = st.text_input("🔍 Filtrar bebida...", key="search_input").lower()
    
    # Lista de bebidas y filtro
    lista_completa = list(st.session_state.menu["🍺 Bebidas"].items())
    lista_filtrada = [p for p in lista_completa if busqueda in p[0].lower()]
    
    # Generar filas de 2 productos compactos
    for i in range(0, len(lista_filtrada), 2):
        c1, c2 = st.columns(2)
        
        # Producto 1
        p1, pre1 = lista_filtrada[i]
        with c1: 
            # El CSS arriba compacta este input
            st.number_input(f"{p1}", min_value=0, step=1, key=f"bebida_{p1}")
        
        # Producto 2 (si existe)
        if i + 1 < len(lista_filtrada):
            p2, pre2 = lista_filtrada[i+1]
            with c2: 
                st.number_input(f"{p2}", min_value=0, step=1, key=f"bebida_{p2}")

    # Cálculo Total Bebidas (incluyendo las ocultas por el filtro)
    total_bebidas_hoy = sum(st.session_state.get(f"bebida_{p}", 0) * pre for p, pre in lista_completa)
    ventas_esperadas += total_bebidas_hoy

    st.divider()
    st.write(f"**Subtotal Bebidas:** ₡{total_bebidas_hoy:,}")

# --- PESTAÑA COMIDAS (Standard) ---
with tab_comida:
    st.subheader("Suma de Comandas")
    monto_comida = st.number_input("Total Ventas de Cocina (₡)", min_value=0, step=500, key="monto_total_comida")
    ventas_esperadas += monto_comida
    st.write(f"**Subtotal Comida:** ₡{monto_comida:,}")

# --- PESTAÑA OTROS (Standard) ---
with tab_otros:
    st.subheader("Otros Productos")
    for prod, precio in st.session_state.menu["📦 Otros"].items():
        c1, c2 = st.columns([2, 1])
        cant = c1.number_input(f"{prod} (₡{precio:,})", min_value=0, key=f"otro_{prod}")
        subtotal = cant * precio
        ventas_esperadas += subtotal
        c2.write(f"₡{subtotal:,}")

# --- PESTAÑA DE CIERRE FINAL ---
with tab_arqueo:
    st.header("🧮 Arqueo de Efectivo")
    col_billetes, col_monedas = st.columns(2)
    total_efectivo = 0
    with col_billetes:
        st.subheader("Billetes")
        for b in [20000, 10000, 5000, 2000, 1000]:
            cant = st.number_input(f"₡{b:,}", min_value=0, step=1, key=f"billete_{b}")
            total_efectivo += (cant * b)
    with col_monedas:
        st.subheader("Monedas")
        for m in [500, 100, 50, 25, 10, 5]:
            cant = st.number_input(f"₡{m}", min_value=0, step=1, key=f"moneda_{m}")
            total_efectivo += (cant * m)

    st.divider()
    sinpe = st.number_input("Total SINPE Móvil", min_value=0, key="pago_sinpe")
    tarjetas = st.number_input("Total Tarjetas (Vouchers)", min_value=0, key="pago_tarjeta")
    pendientes = st.number_input("Pendientes (Fiados)", min_value=0, key="pago_pendientes")
    fondo_inicial = st.number_input("Fondo Inicial (Caja Chica)", min_value=0, key="caja_fondo")

    st.divider()
    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales_hoy = total_reportado - fondo_inicial
    diferencia = ventas_reales_hoy - ventas_esperadas

    st.write(f"### Dinero Físico en Caja: ₡{total_efectivo:,}")
    st.write(f"### Ventas Netas Totales: ₡{ventas_reales_hoy:,}")
    st.write(f"### Venta Esperada: ₡{ventas_esperadas:,}")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("LIMPIAR CIERRE"):
            limpiar_cierre()
            st.rerun()
    with c2:
        if st.button("GUARDAR CIERRE EN EXCEL", type="primary", use_container_width=True):
            fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
            hoja_cierre.append_row([fecha_hoy, ventas_esperadas, total_reportado, diferencia])
            st.success("✅ Cierre guardado exitosamente.")

# --- CONFIGURACIÓN EN SIDEBAR (GESTIÓN DEL MENÚ) ---
st.sidebar.header("⚙️ Configuración")
if st.sidebar.checkbox("Gestionar Productos"):
    st.sidebar.subheader("Añadir")
    cat_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"], key="sidebar_cat_add")
    nom_add = st.sidebar.text_input("Nombre", key=f"in_{st.session_state.reset_key}")
    pre_add = st.sidebar.number_input("Precio", min_value=0, key=f"ip_{st.session_state.reset_key}")
    if st.sidebar.button("➕ Guardar en Excel"):
        if nom_add:
            hoja_prod.append_row([cat_add, nom_add, pre_add])
            st.session_state.reset_key += 1
            if 'menu' in st.session_state:
                del st.session_state.menu # Forzamos recarga desde Excel
            st.sidebar.success(f"¡{nom_add} añadido!")
            st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Eliminar")
    cat_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"], key="sidebar_cat_del")
    prods = list(st.session_state.menu[cat_del].keys())
    if prods:
        prod_del = st.sidebar.selectbox("Producto a borrar", prods)
        if st.sidebar.button("🗑️ Borrar de Excel"):
            # Buscar y borrar fila en Sheets
            try:
                celda = hoja_prod.find(prod_del)
                hoja_prod.delete_rows(celda.row)
                if 'menu' in st.session_state:
                    del st.session_state.menu
                st.sidebar.warning(f"Se eliminó: {prod_del}")
                st.rerun()
            except:
                st.sidebar.error("Error al borrar en Sheets.")
