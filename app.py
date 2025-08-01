import streamlit as st
import pandas as pd
import io
from config import CUENTAS
from cves import asign_cve
from conc import conciliacion
st.title("Conciliación bancaria")

st.header("Arrastra los estados de cuenta")
uploaded_files = {}
dfs_edo_cta = {}
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
# Agregamos los widgets para arrastrar el archivo
for banco, cuentas in CUENTAS.items():
    for cuenta in cuentas:
        uploaded_files[(banco,cuenta)] = cols[(banco,cuenta)].file_uploader(
            f"Cuenta {cuenta}",
            type=['csv', 'xlsx', 'txt'],
            accept_multiple_files=False,
        )
        if uploaded_files[(banco,cuenta)]:
            dfs_edo_cta[(banco,cuenta)] = asign_cve(uploaded_files[(banco,cuenta)],banco,cuenta)
            cols[(banco,cuenta)].markdown('Procesado')
st.header("Arrastra el reporte de caja de SAP")
uploaded_files['sap'] = st.file_uploader(
    'Caja Partidas Individuales',
    type=['csv', 'xlsx'],
    accept_multiple_files=False
)
if uploaded_files['sap']:
    sap_caja = pd.read_excel(uploaded_files['sap'])
    st.markdown('Procesado')

def conciliar(dfs_edo_cta: dict, sap_caja: pd.DataFrame):
   # concatenamos los estados de cuenta
   edo_cta_cves = pd.concat(dfs_edo_cta.values())
   conciliacion(edo_cta_cves=edo_cta_cves, sap_caja=sap_caja)

if len(uploaded_files)>=2:
    if uploaded_files['sap']:
        st.button('Conciliar',on_click=conciliar,args=[uploaded_files, sap_caja])

