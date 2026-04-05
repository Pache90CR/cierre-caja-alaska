import streamlit as st

st.title("💰 Cierre de Caja - Bar Restaurante Alaska")

# Configuración de billetes y monedas de Costa Rica
denominaciones = [20000, 10000, 5000, 2000, 1000, 500, 100, 50, 25, 10, 5]

st.subheader("Conteo de Efectivo (Colones)")
col1, col2 = st.columns(2)
conteo = {}

for i, monto in enumerate(denominaciones):
    # Dividimos en dos columnas para que se vea bien en el celular
    col = col1 if i % 2 == 0 else col2
    conteo[monto] = col.number_input(f"₡{monto}", min_value=0, step=1, key=f"moneda_{monto}")

total_efectivo = sum(m * c for m, c in conteo.items())
st.metric("Total Efectivo", f"₡{total_efectivo:,}")
