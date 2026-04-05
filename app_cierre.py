import streamlit as st

st.set_page_config(page_title="POS Alaska", layout="centered")

# --- ESTADO DE LA APP (Para guardar productos nuevos en la sesión) ---
if 'menu_personalizado' not in st.session_state:
    st.session_state.menu_personalizado = {
        "Bebidas": {"Imperial": 1500, "Pilsen": 1500, "ChiliAlaska": 2000},
        "Comida": {"Hamburguesa": 3500, "Papas Fritas": 2000},
        "Otros": {"Cigarros": 2500}
    }

st.title("🇨🇷 Sistema de Ventas - Alaska")

# --- SECCIÓN: AGREGAR NUEVOS PRODUCTOS ---
with st.expander("➕ Agregar nuevo producto al menú"):
    nueva_cat = st.selectbox("Categoría", ["Bebidas", "Comida", "Otros"])
    nuevo_nombre = st.text_input("Nombre del producto (ej: Heineken)")
    nuevo_precio = st.number_input("Precio (Colones)", min_value=0, step=100)
    
    if st.button("Guardar en Menú"):
        if nuevo_nombre:
            st.session_state.menu_personalizado[nueva_cat][nuevo_nombre] = nuevo_precio
            st.success(f"{nuevo_nombre} agregado!")
            st.rerun()

# --- SECCIÓN: REGISTRO DE VENTAS ---
st.header("📝 Registro de Hoy")
tab1, tab2, tab3 = st.tabs(["🍺 Bebidas", "🍔 Comida", "📦 Otros"])

ventas_totales = 0

def mostrar_categoria(categoria, tab_obj):
    global ventas_totales
    with tab_obj:
        for prod, precio in st.session_state.menu_personalizado[categoria].items():
            col1, col2 = st.columns([2, 1])
            cant = col1.number_input(f"{prod} (₡{precio:,})", min_value=0, step=1, key=f"v_{prod}")
            subtotal = cant * precio
            ventas_totales += subtotal
            col2.write(f"Sub: ₡{subtotal:,}")

mostrar_categoria("Bebidas", tab1)
mostrar_categoria("Comida", tab2)
mostrar_categoria("Otros", tab3)

st.divider()
st.metric("VENTA TOTAL ESPERADA", f"₡{ventas_totales:,}")

# --- SECCIÓN: EL CUADRE FINAL ---
st.header("💰 Cuadre de Caja")
sinpe = st.number_input("Total recibido por SINPE", min_value=0)
tarjetas = st.number_input("Total Vouchers Tarjeta", min_value=0)
efectivo_contado = st.number_input("Efectivo total en la gaveta", min_value=0)
fondo_inicial = st.number_input("Fondo inicial (cambio)", min_value=0)

# El dinero real que entró hoy
dinero_real = (efectivo_contado + sinpe + tarjetas) - fondo_inicial
diferencia = dinero_real - ventas_totales

if st.button("CALCULAR CIERRE"):
    st.subheader(f"Resultado: ₡{dinero_real:,}")
    if diferencia == 0:
        st.success("✅ Caja Cuadrada")
    elif diferencia > 0:
        st.warning(f"⚠️ Sobrante: ₡{diferencia:,}")
    else:
        st.error(f"❌ Faltante: ₡{abs(diferencia):,}")
