import streamlit as st
import pandas as pd
import io
from config import CUENTAS
st.title("Prueba conciliación")

st.header("Arrastra los estados de cuenta")
uploaded_files = {}
# Creamos las tabs por banco
tabs = st.tabs(CUENTAS.keys())
tab_dict = {banco: t for banco,t in zip(CUENTAS.keys(),tabs)}
# Creamos las columnas contenedor
cols = {(b,c):None for b,ctas in CUENTAS.items() for c in ctas}
for banco, cuentas in CUENTAS.items():
    # tab_dict[banco].subheader(banco)
    col_list = tab_dict[banco].columns(len(cuentas))
    for i,cuenta in enumerate(cuentas):
        cols[(banco,cuenta)]= col_list[i]
# Agregamos los widget para arrastrar el archivo
for banco, cuentas in CUENTAS.items():
    for cuenta in cuentas:
        uploaded_files[(banco,cuenta)] = cols[(banco,cuenta)].file_uploader(
            f"Cuenta {cuenta}",
            type=['csv', 'xlsx', 'txt'],
            accept_multiple_files=False,
        )

st.header("Arrastra el reporte de caja de SAP")
uploaded_files['sap'] = st.file_uploader(
    'Caja Partidas Individuales',
    type=['csv', 'xlsx'],
    accept_multiple_files=False
)
def conciliar(files: dict):
    for banco,cuentas in CUENTAS.items():
        for cuenta in cuentas:
            if files[(banco,cuenta)]:
                st.markdown(f'Cuenta {cuenta} de {banco} procesada...')
    if files['sap']:
        st.markdown('Reporte de SAP procesado.')

if len(uploaded_files)>=2:
    if uploaded_files['sap']:
        st.button('Conciliar',on_click=conciliar,args=uploaded_files)

