import streamlit as st

st.set_page_config(page_title="Cierre Alaska", layout="centered")

# --- BASE DE DATOS DE BEBIDAS Y OTROS ---
if 'menu' not in st.session_state:
    st.session_state.menu = {
        "🍺 Bebidas": {"Imperial": 1500, "Pilsen": 1500, "ChiliAlaska": 2000},
        "📦 Otros": {"Cigarros": 2500, "Snacks": 1000}
    }

st.title("💰 Gestión de Caja - Alaska")

# --- PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍳 Ventas Comida", "📦 Otros", "📉 CIERRE FINAL"
])

ventas_esperadas = 0

# 1. PESTAÑA BEBIDAS (Sigue por unidades)
with tab_bebidas:
    st.subheader("Conteo de Bebidas")
    for prod, precio in st.session_state.menu["🍺 Bebidas"].items():
        c1, c2 = st.columns([2, 1])
        cant = c1.number_input(f"{prod} (₡{precio:,})", min_value=0, key=f"v_{prod}")
        subtotal = cant * precio
        ventas_esperadas += subtotal
        c2.write(f"₡{subtotal:,}")

# 2. PESTAÑA COMIDA (SIMPLIFICADA A MONTO TOTAL)
with tab_comida:
    st.subheader("Suma de Comandas")
    st.info("Ingresa el monto total sumado de todas las comandas de comida del día.")
    monto_comida = st.number_input("Total Ventas de Cocina (₡)", min_value=0, step=500, key="total_comida")
    ventas_esperadas += monto_comida
    st.write(f"**Subtotal Comida:** ₡{monto_comida:,}")

# 3. PESTAÑA OTROS
with tab_otros:
    st.subheader("Otros Productos")
    for prod, precio in st.session_state.menu["📦 Otros"].items():
        c1, c2 = st.columns([2, 1])
        cant = c1.number_input(f"{prod} (₡{precio:,})", min_value=0, key=f"v_{prod}")
        subtotal = cant * precio
        ventas_esperadas += subtotal
        c2.write(f"₡{subtotal:,}")

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
    pendientes = st.number_input("Pendientes (Créditos/Fiados)", min_value=0)
    fondo_inicial = st.number_input("Fondo Inicial (Caja Chica)", min_value=0)

    # CÁLCULOS FINALES
    st.divider()
    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales_hoy = total_reportado - fondo_inicial
    diferencia = ventas_reales_hoy - ventas_esperadas

    st.write(f"### Dinero Físico en Caja: ₡{total_efectivo:,}")
    st.write(f"### Ventas Netas Totales: ₡{ventas_reales_hoy:,}")
    st.write(f"### Venta Esperada (Bebidas + Comandas): ₡{ventas_esperadas:,}")
    
    if st.button("REALIZAR CONCILIACIÓN"):
        if diferencia == 0:
            st.success("🎯 ¡Perfecto! La caja cuadra exactamente.")
        elif diferencia > 0:
            st.warning(f"📈 Sobrante: ₡{diferencia:,}")
        else:
            st.error(f"📉 Faltante: ₡{abs(diferencia):,}")

# --- CONFIGURACIÓN EN SIDEBAR (Solo para Bebidas y Otros) ---
st.sidebar.header("⚙️ Configuración")
if st.sidebar.checkbox("Gestionar Productos (Bebidas/Otros)"):
    # Agregar
    st.sidebar.subheader("Añadir")
    cat_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    nom_add = st.sidebar.text_input("Nombre")
    pre_add = st.sidebar.number_input("Precio", min_value=0)
    if st.sidebar.button("Guardar"):
        st.session_state.menu[cat_add][nom_add] = pre_add
        st.rerun()
    
    # Eliminar
    st.sidebar.subheader("Eliminar")
    cat_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"])
    prod_del = st.sidebar.selectbox("Producto", list(st.session_state.menu[cat_del].keys()))
    if st.sidebar.button("🗑️ Eliminar"):
        del st.session_state.menu[cat_del][prod_del]
        st.rerun()

st.set_page_config(page_title="Cierre Alaska", layout="centered")

# --- BASE DE DATOS DE BEBIDAS Y OTROS ---
if 'menu' not in st.session_state:
    st.session_state.menu = {
        "🍺 Bebidas": {"Imperial": 1500, "Pilsen": 1500, "ChiliAlaska": 2000},
        "📦 Otros": {"Cigarros": 2500, "Snacks": 1000}
    }

st.title("💰 Gestión de Caja - Alaska")

# --- PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍳 Ventas Comida", "📦 Otros", "📉 CIERRE FINAL"
])

ventas_esperadas = 0

# 1. PESTAÑA BEBIDAS (Sigue por unidades)
with tab_bebidas:
    st.subheader("Conteo de Bebidas")
    for prod, precio in st.session_state.menu["🍺 Bebidas"].items():
        c1, c2 = st.columns([2, 1])
        cant = c1.number_input(f"{prod} (₡{precio:,})", min_value=0, key=f"v_{prod}")
        subtotal = cant * precio
        ventas_esperadas += subtotal
        c2.write(f"₡{subtotal:,}")

# 2. PESTAÑA COMIDA (SIMPLIFICADA A MONTO TOTAL)
with tab_comida:
    st.subheader("Suma de Comandas")
    st.info("Ingresa el monto total sumado de todas las comandas de comida del día.")
    monto_comida = st.number_input("Total Ventas de Cocina (₡)", min_value=0, step=500, key="total_comida")
    ventas_esperadas += monto_comida
    st.write(f"**Subtotal Comida:** ₡{monto_comida:,}")

# 3. PESTAÑA OTROS
with tab_otros:
    st.subheader("Otros Productos")
    for prod, precio in st.session_state.menu["📦 Otros"].items():
        c1, c2 = st.columns([2, 1])
        cant = c1.number_input(f"{prod} (₡{precio:,})", min_value=0, key=f"v_{prod}")
        subtotal = cant * precio
        ventas_esperadas += subtotal
        c2.write(f"₡{subtotal:,}")

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
    pendientes = st.number_input("Pendientes (Créditos/Fiados)", min_value=0)
    fondo_inicial = st.number_input("Fondo Inicial (Caja Chica)", min_value=0)

    # CÁLCULOS FINALES
    st.divider()
    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales_hoy = total_reportado - fondo_inicial
    diferencia = ventas_reales_hoy - ventas_esperadas

    st.write(f"### Dinero Físico en Caja: ₡{total_efectivo:,}")
    st.write(f"### Ventas Netas Totales: ₡{ventas_reales_hoy:,}")
    st.write(f"### Venta Esperada (Bebidas + Comandas): ₡{ventas_esperadas:,}")
    
    if st.button("REALIZAR CONCILIACIÓN"):
        if diferencia == 0:
            st.success("🎯 ¡Perfecto! La caja cuadra exactamente.")
        elif diferencia > 0:
            st.warning(f"📈 Sobrante: ₡{diferencia:,}")
        else:
            st.error(f"📉 Faltante: ₡{abs(diferencia):,}")

# --- CONFIGURACIÓN EN SIDEBAR (Solo para Bebidas y Otros) ---
st.sidebar.header("⚙️ Configuración")
if st.sidebar.checkbox("Gestionar Productos (Bebidas/Otros)"):
    # Agregar
    st.sidebar.subheader("Añadir")
    cat_add = st.sidebar.selectbox("Categoría", ["🍺 Bebidas", "📦 Otros"])
    nom_add = st.sidebar.text_input("Nombre")
    pre_add = st.sidebar.number_input("Precio", min_value=0)
    if st.sidebar.button("Guardar"):
        st.session_state.menu[cat_add][nom_add] = pre_add
        st.rerun()
    
    # Eliminar
    st.sidebar.subheader("Eliminar")
    cat_del = st.sidebar.selectbox("Categoría ", ["🍺 Bebidas", "📦 Otros"])
    prod_del = st.sidebar.selectbox("Producto", list(st.session_state.menu[cat_del].keys()))
    if st.sidebar.button("🗑️ Eliminar"):
        del st.session_state.menu[cat_del][prod_del]
        st.rerun()
