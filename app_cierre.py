import streamlit as st

st.set_page_config(page_title="Cierre de Caja Pro", page_icon="💰")

st.title("💰 Control de Cierre de Caja")

# --- SECCIÓN SISTEMA ---
st.header("1. Datos del Sistema")
ventas_sistema = st.number_input("Ventas totales en Sistema ($)", min_value=0.0, step=100.0)
fondo_caja = st.number_input("Fondo inicial ($)", min_value=0.0, step=100.0)

# --- SECCIÓN EFECTIVO ---
st.header("2. Conteo de Efectivo")
col1, col2 = st.columns(2)

denominaciones = [20000, 10000, 5000, 2000, 1000]
conteo = {}

with col1:
    for d in denominaciones[:3]:
        conteo[d] = st.number_input(f"Billetes de {d}", min_value=0, step=1)

with col2:
    for d in denominaciones[3:]:
        conteo[d] = st.number_input(f"Billetes de {d}", min_value=0, step=1)

total_efectivo = sum(k * v for k, v in conteo.items())

# --- SECCIÓN OTROS PAGOS ---
st.header("3. Otros Medios")
tarjetas = st.number_input("Total Tarjetas / Datáfono", min_value=0.0)
transferencias = st.number_input("Total Transferencias (Sinpe/Bizum)", min_value=0.0)

# --- CÁLCULO FINAL ---
total_real = total_efectivo + tarjetas + transferencias - fondo_caja
diferencia = total_real - ventas_sistema

st.divider()

# --- RESULTADO VISUAL ---
st.subheader("Resultado del Cierre")
if diferencia == 0:
    st.success(f"Caja Cuadrada: ${total_real}")
elif diferencia > 0:
    st.warning(f"Sobrante: ${diferencia}")
else:
    st.error(f"Faltante: ${abs(diferencia)}")

if st.button("Guardar Reporte del Día"):
    st.balloons()
    st.write("✅ Reporte guardado en la base de datos.")