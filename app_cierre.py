import streamlit as st

st.set_page_config(page_title="Cierre Alaska", page_icon="🍺")

st.title("📊 Cierre de Caja: Ventas por Producto")

# 1. Definición de productos y precios (Puedes cambiar los precios aquí)
# Esto actúa como tu base de datos de precios
precios_productos = {
    "Imperial": 1500, # Precio ejemplo en colones
    "Pilsen": 1500,
    "ChiliAlaska": 2000,
    "Hamburguesa La Chinita": 3500,
    "Refrescos": 1000
}

st.subheader("📝 Registro de Unidades Vendidas")
ventas_totales_productos = 0

# Creamos filas para cada producto
for producto, precio in precios_productos.items():
    col_nombre, col_cantidad, col_subtotal = st.columns([2, 1, 1])
    
    with col_nombre:
        st.write(f"**{producto}** (₡{precio:,})")
    
    with col_cantidad:
        unidades = st.number_input(f"Cant. {producto}", min_value=0, step=1, label_visibility="collapsed")
    
    subtotal = unidades * precio
    ventas_totales_productos += subtotal
    
    with col_subtotal:
        st.write(f"₡{subtotal:,}")

st.divider()
st.metric("VENTA TOTAL ESPERADA", f"₡{ventas_totales_productos:,}")

# 2. Sección de Validación (Efectivo vs Sistema)
st.subheader("💰 Validación de Efectivo")
efectivo_fisico = st.number_input("¿Cuánto dinero físico hay en caja?", min_value=0)

diferencia = efectivo_fisico - ventas_totales_productos

if diferencia == 0:
    st.success("✅ ¡Caja Cuadrada!")
elif diferencia > 0:
    st.warning(f"⚠️ Sobrante: ₡{diferencia:,}")
else:
    st.error(f"❌ Faltante: ₡{abs(diferencia):,}")
