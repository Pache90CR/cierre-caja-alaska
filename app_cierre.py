import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cierre Alaska", layout="centered")

# CSS QUIRÚRGICO PARA ALINEAR EL NÚMERO A LA IZQUIERDA (SOLO BEBIDAS)
st.markdown("""
    <style>
    /* Compactar el cuadro y alinear el número a la izquierda */
    div[data-testid="stNumberInput"] input {
        text-align: left !important;
        padding-left: 10px !important;
    }
    /* Reducir el ancho máximo del control para que no se estire innecesariamente */
    div[data-testid="stNumberInput"] {
        max-width: 150px !important;
    }
    /* Estilo para la tarjeta de ganancia */
    .ganancia-card { 
        background-color: #1e2129; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #2ecc71; 
    }
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

# --- 2. GESTIÓN DE DATOS ---
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

# --- PESTAÑA BEBIDAS ---
with tab_bebidas:
    st.subheader("Selección de Bebidas")
    busqueda = st.text_input("🔍 Filtrar bebida...", key="search_input").lower()
    lista_completa = list(st.session_state.menu["🍺 Bebidas"].items())
    lista_filtrada = [p for p in lista_completa if busqueda in p[0].lower()]
    for p, v in lista_filtrada:
        st.number_input(f"{p}", min_value=0, step=1, key=f"bebida_{p}")
    for p, v in lista_completa:
        cant = st.session_state.get(f"bebida_{p}", 0)
        ventas_esperadas += (cant * v[0])
        costos_totales += (cant * v[1])

# --- PESTAÑA COMIDAS ---
with tab_comida:
    monto_comida = st.number_input("Total Comandas Cocina (₡)", min_value=0, step=500, key="monto_total_comida")
    ventas_esperadas += monto_comida
    costos_totales += (monto_comida * 0.6)

# --- PESTAÑA OTROS ---
with tab_otros:
    lista_o = list(st.session_state.menu["📦 Otros"].items())
    for p, v in lista_o:
        cant = st.number_input(f"{p} (₡{v[0]:,})", min_value=0, key=f"otro_{p}")
        ventas_esperadas += (cant * v[0])
        costos_totales += (cant * v[1])

# --- PESTAÑA ARQUEO ---
with tab_arqueo:
    st.header("🧮 Arqueo de Caja")
    col_b, col_m = st.columns(2)
    total_efectivo = 0
    with col_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            total_efectivo += st.number_input(f"₡{b:,}", min_value=0, key=f"billete_{b}") * b
    with col_m:
        for m in [500, 100, 50]:
            total_efectivo += st.number_input(f"₡{m}", min_value=0, key=f"moneda_{m}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE", min_value=0, key="pago_sinpe")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, key="pago_tarjeta")
    pendientes = st.number_input("Pendientes (Fiados)", min_value=0, key="pago_pendientes")
    fondo = st.number_input("Fondo Inicial", min_value=0, key="caja_fondo")

    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales = total_reportado - fondo
    dif = ventas_reales - ventas_esperadas

    st.write(f"### Venta Neta: ₡{ventas_reales:,} | Esperada: ₡{ventas_esperadas:,}")
    
    if st.button("💾 GUARDAR CIERRE EN EXCEL", use_container_width=True):
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        ganancia_dia = ventas_reales - costos_totales
        # Guardamos en el orden: Fecha, Venta, Ganancia, Diferencia
        hoja_cierre.append_row([fecha, ventas_reales, ganancia_dia, dif])
        st.success("✅ Cierre guardado correctamente.")

# --- PESTAÑA GANANCIAS CON GRÁFICA MENSUAL ---
with tab_ganancia:
    st.header("📊 Análisis de Ganancias")
    
    # Ganancia del momento (basada en lo que está marcado arriba)
    ganancia_ahora = ventas_esperadas - costos_totales
    st.markdown(f"""
    <div class='ganancia-card'>
        <h3>Ganancia Proyectada del Cierre Actual</h3>
        <h1 style='color: #2ecc71;'>₡{ganancia_ahora:,}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.subheader("Comparativa por Mes")
    
    # Cargar datos históricos del Excel para la gráfica
    try:
        registros = hoja_cierre.get_all_records()
        if registros:
            df = pd.DataFrame(registros)
            
            # Asegurar que los nombres de columnas coincidan con tu Excel
            # (Ajustar si tus columnas se llaman distinto)
            col_fecha = df.columns[0]   # Fecha
            col_ganancia = df.columns[2] # Ganancia
            
            # Convertir fecha a formato real y agrupar por mes
            df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True)
            df['Mes'] = df[col_fecha].dt.strftime('%Y-%m') # Ejemplo: 2024-05
            
            # Sumar ganancias por mes
            resumen_mensual = df.groupby('Mes')[col_ganancia].sum().reset_index()
            
            # Mostrar gráfica
            st.bar_chart(data=resumen_mensual, x='Mes', y=col_ganancia, color="#2ecc71")
            
            # Tabla de datos para ver los números exactos
            st.dataframe(resumen_mensual, use_container_width=True)
        else:
            st.info("Aún no hay datos guardados para mostrar la gráfica.")
    except Exception as e:
        st.error(f"No se pudo cargar la gráfica: {e}")

# --- SIDEBAR (GESTIÓN) ---
st.sidebar.header("🧹 Acciones")
if st.sidebar.button("LIMPIAR CIERRE"):
    for key in list(st.session_state.keys()):
        if key.startswith(('bebida_', 'otro_', 'billete_', 'moneda_', 'pago_', 'monto_total_comida')):
            st.session_state[key] = 0
    st.rerun()

if st.sidebar.checkbox("⚙️ Gestionar Menú"):
    st.sidebar.subheader("Añadir Producto")
    cat_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    nom_add = st.sidebar.text_input("Nombre", key=f"n_{st.session_state.reset_key}")
    pre_add = st.sidebar.number_input("Precio", min_value=0, key=f"p_{st.session_state.reset_key}")
    cos_add = st.sidebar.number_input("Costo", min_value=0, key=f"c_{st.session_state.reset_key}")
    if st.sidebar.button("➕ Guardar"):
        if nom_add:
            hoja_prod.append_row([cat_add, nom_add, pre_add, cos_add])
            st.session_state.reset_key += 1
            del st.session_state.menu
            st.rerun()
    st.sidebar.divider()
    if 'menu' in st.session_state:
        cat_del = st.sidebar.selectbox("Borrar de:", ["🍺 Bebidas", "📦 Otros"])
        prods = list(st.session_state.menu[cat_del].keys())
        if prods:
            prod_del = st.sidebar.selectbox("Producto", prods)
            if st.sidebar.button("🗑️ Eliminar"):
                celda = hoja_prod.find(prod_del)
                hoja_prod.delete_rows(celda.row)
                del st.session_state.menu
                st.rerun()
