import streamlit as st

st.set_page_config(page_title="Cierre Alaska", layout="centered")

# --- 1. INICIALIZACIÓN DE LA MEMORIA (SESSION STATE) ---
if 'menu' not in st.session_state:
    st.session_state.menu = {
        "🍺 Bebidas": {"Imperial": 1500, "Pilsen": 1500, "ChiliAlaska": 2000},
        "📦 Otros": {"Cigarros": 2500, "Snacks": 1000}
    }

if 'count_add' not in st.session_state:
    st.session_state.count_add = 0

# --- 2. FUNCIÓN PARA LIMPIAR TODO ---
def limpiar_cierre():
    # Buscamos todas las llaves que guardan montos y las ponemos en 0
    for key in st.session_state.keys():
        if key.startswith(('bebida_', 'otro_', 'billete_', 'moneda_', 'pago_', 'monto_total_comida')):
            st.session_state[key] = 0
    st.toast("✅ Todos los campos se han reiniciado", icon="🧹")

st.title("💰 Gestión de Caja - Alaska")

# --- 3. BOTÓN DE LIMPIEZA EN EL SIDEBAR ---
st.sidebar.header("🧹 Acciones")
if st.sidebar.button("LIMPIAR TODO EL CIERRE", use_container_width=True, type="primary"):
    limpiar_cierre()
    st.rerun()

# --- 4. PESTAÑAS ---
tab_bebidas, tab_comida, tab_otros, tab_arqueo = st.tabs([
    "🍺 Bebidas", "🍳 Ventas Comida", "📦 Otros", "📉 CIERRE FINAL"
])

ventas_esperadas = 0

# --- PESTAÑA BEBIDAS (Buscador + 2 Columnas) ---
with tab_bebidas:
    st.subheader("Selección de Bebidas")
    busqueda = st.text_input("🔍 Filtrar bebida...", key="search_input").lower()
    
    lista_completa = list(st.session_state.menu["🍺 Bebidas"].items())
    lista_filtrada = [p for p in lista_completa if busqueda in p[0].lower()]
    
    if not lista_filtrada:
        st.warning("No se encontraron coincidencias.")
    else:
        for i in range(0, len(lista_filtrada), 2):
            c1, c2 = st.columns(2)
            p1, pre1 = lista_filtrada[i]
            with c1:
                st.number_input(f"{p1} (₡{pre1:,})", min_value=0, step=1, key=f"bebida_{p1}")
            if i + 1 < len(lista_filtrada):
                p2, pre2 = lista_filtrada[i+1]
                with c2:
                    st.number_input(f"{p2} (₡{pre2:,})", min_value=0, step=1, key=f"bebida_{p2}")

    # Cálculo total de bebidas (incluyendo las ocultas por el filtro)
    total_bebidas = sum(st.session_state.get(f"bebida_{p}", 0) * pre for p, pre in lista_completa)
    ventas_esperadas += total_bebidas
    st.write(f"**Subtotal Bebidas:** ₡{total_bebidas:,}")

# --- PESTAÑA COMIDA ---
with tab_comida:
    st.subheader("Suma de Comandas")
    monto_comida = st.number_input("Total Ventas de Cocina (₡)", min_value=0, step=500, key="monto_total_comida")
    ventas_esperadas += monto_comida

# --- PESTAÑA OTROS (2 Columnas) ---
with tab_otros:
    st.subheader("Otros Productos")
    lista_otros = list(st.session_state.menu["📦 Otros"].items())
    for i in range(0, len(lista_otros), 2):
        c1, c2 = st.columns(2)
        p1, pre1 = lista_otros[i]
        with c1:
            st.number_input(f"{p1} (₡{pre1:,})", min_value=0, step=1, key=f"otro_{p1}")
        if i + 1 < len(lista_otros):
            p2, pre2 = lista_otros[i+1]
            with c2:
                st.number_input(f"{p2} (₡{pre2:,})", min_value=0, step=1, key=f"otro_{p2}")
    
    total_otros = sum(st.session_state.get(f"otro_{p}", 0) * pre for p, pre in lista_otros)
    ventas_esperadas += total_otros

# --- PESTAÑA CIERRE FINAL ---
with tab_arqueo:
    st.header("🧮 Arqueo de Efectivo")
    col_b, col_m = st.columns(2)
    total_efectivo = 0
    with col_b:
        for b in [20000, 10000, 5000, 2000, 1000]:
            total_efectivo += st.number_input(f"₡{b:,}", min_value=0, step=1, key=f"billete_{b}") * b
    with col_m:
        for m in [500, 100, 50, 25, 10, 5]:
            total_efectivo += st.number_input(f"₡{m}", min_value=0, step=1, key=f"moneda_{m}") * m

    st.divider()
    sinpe = st.number_input("Total SINPE Móvil", min_value=0, key="pago_sinpe")
    tarjetas = st.number_input("Total Tarjetas", min_value=0, key="pago_tarjeta")
    pendientes = st.number_input("Pendientes (Fiados)", min_value=0, key="pago_pendientes")
    fondo = st.number_input("Fondo Inicial", min_value=0, key="caja_fondo")

    total_reportado = total_efectivo + sinpe + tarjetas + pendientes
    ventas_reales = total_reportado - fondo
    dif = ventas_reales - ventas_esperadas

    st.write(f"### Venta Neta: ₡{ventas_reales:,} | Esperada: ₡{ventas_esperadas:,}")
    if st.button("CONCILIAR", key="btn_final"):
        if dif == 0: st.success("🎯 Caja Cuadrada")
        elif dif > 0: st.warning(f"📈 Sobrante: ₡{dif:,}")
        else: st.error(f"📉 Faltante: ₡{abs(dif):,}")

# --- SIDEBAR: GESTIÓN DE PRODUCTOS ---
st.sidebar.divider()
if st.sidebar.checkbox("⚙️ Configurar Productos"):
    
    # SECCIÓN AÑADIR
    st.sidebar.subheader("Añadir")
    cat_add = st.sidebar.selectbox("Categoría a añadir", ["🍺 Bebidas", "📦 Otros"], key="cat_add_sidebar")
    nom_add = st.sidebar.text_input("Nombre", key=f"add_n_{st.session_state.count_add}")
    pre_add = st.sidebar.number_input("Precio", min_value=0, key=f"add_p_{st.session_state.count_add}")
    
    if st.sidebar.button("Guardar Producto", use_container_width=True):
        if nom_add:
            st.session_state.menu[cat_add][nom_add] = pre_add
            st.session_state.count_add += 1
            st.sidebar.success(f"¡{nom_add} añadido!")
            st.rerun()

    st.sidebar.divider()

    # SECCIÓN ELIMINAR
    st.sidebar.subheader("Eliminar")
    cat_del = st.sidebar.selectbox("Categoría a limpiar", ["🍺 Bebidas", "📦 Otros"], key="cat_del_sidebar")
    
    # Solo mostramos el selector si hay productos en esa categoría
    opciones_del = list(st.session_state.menu[cat_del].keys())
    
    if opciones_del:
        prod_del = st.sidebar.selectbox("Selecciona producto a borrar", opciones_del, key="prod_del_sidebar")
        
        if st.sidebar.button("🗑️ ELIMINAR PERMANENTE", use_container_width=True, type="secondary"):
            del st.session_state.menu[cat_del][prod_del]
            st.sidebar.warning(f"Se eliminó: {prod_del}")
            st.rerun()
    else:
        st.sidebar.info("No hay productos para eliminar en esta categoría.")
