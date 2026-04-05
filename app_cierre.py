import streamlit as st

st.set_page_config(page_title="Cierre Alaska", layout="centered")

# --- BASE DE DATOS TEMPORAL ---
if 'menu' not in st.session_state:
    st.session_state.menu = {
        "🍺 Bebidas": {"Imperial": 1500, "Pilsen": 1500, "ChiliAlaska": 2000},
        "🍔 Comida": {"Hamburguesa": 3500, "Papas": 2000},
        "📦 Otros": {"Cigarros": 2500}
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
    
    st.subheader("💳 Otros Ingresos")
    sinpe = st.number_input("Total SINPE Móvil", min_value=0)
    tarjetas = st.number_input("Total Tarjetas (Vouchers)", min_value=0)
    fondo_inicial = st.number_input("Fondo Inicial (Caja Chica)", min_value=0)

    # CÁLCULOS FINALES
    st.divider()
    total_en_mano = total_efectivo + sinpe + tarjetas
    ventas_reales_hoy = total_en_mano - fondo_inicial
    diferencia = ventas_reales_hoy - ventas_esperadas

    st.write(f"### Dinero Físico Total: ₡{total_efectivo:,}")
    st.write(f"### Venta Neta (Sin fondo): ₡{ventas_reales_hoy:,}")
    
    if st.button("REALIZAR CONCILIACIÓN"):
        if diferencia == 0:
            st.success("🎯 ¡Perfecto! La caja cuadra exactamente.")
        elif diferencia > 0:
            st.warning(f"📈 Sobrante: ₡{diferencia:,}. Revisa si olvidaste anotar una venta.")
        else:
            st.error(f"📉 Faltante: ₡{abs(diferencia):,}. ¡Cuidado!")

    # Botón para agregar productos (ahora al final o en sidebar)
    if st.sidebar.checkbox("Configuración: Agregar Productos"):
        st.sidebar.subheader("Nuevo Producto")
        cat = st.sidebar.selectbox("Categoría", list(st.session_state.menu.keys()))
        nom = st.sidebar.text_input("Nombre")
        pre = st.sidebar.number_input("Precio", min_value=0)
        if st.sidebar.button("Añadir"):
            st.session_state.menu[cat][nom] = pre
            st.rerun()import streamlit as st

st.set_page_config(page_title="Cierre Alaska", layout="centered")

# --- BASE DE DATOS TEMPORAL ---
if 'menu' not in st.session_state:
    st.session_state.menu = {
        "🍺 Bebidas": {"Imperial": 1500, "Pilsen": 1500, "ChiliAlaska": 2000},
        "🍔 Comida": {"Hamburguesa": 3500, "Papas": 2000},
        "📦 Otros": {"Cigarros": 2500}
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
    
    st.subheader("💳 Otros Ingresos")
    sinpe = st.number_input("Total SINPE Móvil", min_value=0)
    tarjetas = st.number_input("Total Tarjetas (Vouchers)", min_value=0)
    fondo_inicial = st.number_input("Fondo Inicial (Caja Chica)", min_value=0)

    # CÁLCULOS FINALES
    st.divider()
    total_en_mano = total_efectivo + sinpe + tarjetas
    ventas_reales_hoy = total_en_mano - fondo_inicial
    diferencia = ventas_reales_hoy - ventas_esperadas

    st.write(f"### Dinero Físico Total: ₡{total_efectivo:,}")
    st.write(f"### Venta Neta (Sin fondo): ₡{ventas_reales_hoy:,}")
    
    if st.button("REALIZAR CONCILIACIÓN"):
        if diferencia == 0:
            st.success("🎯 ¡Perfecto! La caja cuadra exactamente.")
        elif diferencia > 0:
            st.warning(f"📈 Sobrante: ₡{diferencia:,}. Revisa si olvidaste anotar una venta.")
        else:
            st.error(f"📉 Faltante: ₡{abs(diferencia):,}. ¡Cuidado!")

    # Botón para agregar productos (ahora al final o en sidebar)
    if st.sidebar.checkbox("Configuración: Agregar Productos"):
        st.sidebar.subheader("Nuevo Producto")
        cat = st.sidebar.selectbox("Categoría", list(st.session_state.menu.keys()))
        nom = st.sidebar.text_input("Nombre")
        pre = st.sidebar.number_input("Precio", min_value=0)
        if st.sidebar.button("Añadir"):
            st.session_state.menu[cat][nom] = pre
            st.rerun()
