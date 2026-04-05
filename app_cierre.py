import streamlit as st

st.set_page_config(page_title="Cierre Alaska", layout="centered")

# --- BASE DE DATOS TEMPORAL ---
if 'menu' not in st.session_state:
    st.session_state.menu = {
        "🍺 Bebidas": {"Imperial": 1300, "Pilsen": 1500, "ChiliAlaska"},
        "🍔 Comida": {"Hamburguesa": 3500, "Papas": 2000},
        "📦 Otros": {"Cigarros": 200}
    }

st.title("💰 Gestión de Caja - Alaska")

# --- PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍔 Comida", "📦 Otros", "📉 CIERRE FINAL"
])

ventas_esperadas = 0

# Función para renderizar ventas
def render_ventas(categoria, tab):
    global ventas_esperadas
    with tab:
        for prod, precio in st.session_state.menu[categoria].items():
            c1, c2 = st.columns([2, 1])
            cant = c1.number_input(f"{prod} (₡{precio:,})", min_value=0, key=f"v_{prod}")
            subtotal = cant * precio
            ventas_esperadas += subtotal
            c2.write(f"₡{subtotal:,}")

render_ventas("🍺 Bebidas", tab_bebidas)
render_ventas("🍔 Comida", tab_comida)
render_ventas("📦 Otros", tab_otros)

# --- PESTAÑA DE CIERRE Y ARQUEO ---
with tab_arqueo:
    st.header("🧮 Arqueo de Efectivo")
    
    col_billetes, col_monedas = st.columns(2)
    total_efectivo = 0
    
    with col_billetes:
        st.subheader("Billetes")
        for b in [20000, 10000, 5000, 2000, 1000]:
            cant = st.number_input(f"₡{b:,}", min_value=0, step=1, key=f"b_{b}")
            total_efectivo += (cant * b)
            
    with col_monedas:
        st.subheader("Monedas")
        for m in [500, 100, 50, 25, 10, 5]:
            cant = st.number_input(f"₡{m}", min_value=0, step=1, key=f"m_{m}")
            total_efectivo += (cant * m)

    st.divider()
    st.subheader("💳 Otros Ingresos y Créditos")
    sinpe = st.number_input("Total SINPE Móvil", min_value=0)
    tarjetas = st.number_input("Total Tarjetas (Vouchers)", min_value=0)
    pendientes = st.number_input("Pendientes (Créditos/Fiados del día)", min_value=0, help="Ventas realizadas que aún no se han cobrado.")
    fondo_inicial = st.number_input("Fondo Inicial (Caja Chica)", min_value=0)

    # CÁLCULOS FINALES
    st.divider()
    # El "Total Reportado" incluye lo que hay en dinero + lo que te deben (pendientes)
    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales_hoy = total_reportado - fondo_inicial
    diferencia = ventas_reales_hoy - ventas_esperadas

    st.write(f"### Dinero Físico en Caja: ₡{total_efectivo:,}")
    st.write(f"### Ventas Netas (Incluye Pendientes): ₡{ventas_reales_hoy:,}")
    st.write(f"### Venta Esperada según Productos: ₡{ventas_esperadas:,}")
    
    if st.button("REALIZAR CONCILIACIÓN"):
        if diferencia == 0:
            st.success("🎯 ¡Perfecto! La caja cuadra exactamente.")
        elif diferencia > 0:
            st.warning(f"📈 Sobrante: ₡{diferencia:,}")
        else:
            st.error(f"📉 Faltante: ₡{abs(diferencia):,}")

# --- CONFIGURACIÓN EN SIDEBAR ---
st.sidebar.header("⚙️ Configuración de Menú")

# Opción para Agregar
if st.sidebar.checkbox("Añadir Producto"):
    st.sidebar.subheader("Nuevo Producto")
    cat_add = st.sidebar.selectbox("Categoría a añadir", list(st.session_state.menu.keys()))
    nom_add = st.sidebar.text_input("Nombre del producto")
    pre_add = st.sidebar.number_input("Precio", min_value=0, key="add_price")
    if st.sidebar.button("Guardar"):
        if nom_add:
            st.session_state.menu[cat_add][nom_add] = pre_add
            st.rerun()

# Opción para Eliminar
if st.sidebar.checkbox("Eliminar Producto"):
    st.sidebar.subheader("Borrar Producto")
    cat_del = st.sidebar.selectbox("Categoría del producto", list(st.session_state.menu.keys()))
    prod_del = st.sidebar.selectbox("Producto a eliminar", list(st.session_state.menu[cat_del].keys()))
    if st.sidebar.button("🗑️ Confirmar Eliminación"):
        del st.session_state.menu[cat_del][prod_del]
        st.sidebar.success(f"Eliminado: {prod_del}")
        st.rerun()
