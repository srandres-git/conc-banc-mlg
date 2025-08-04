import streamlit as st
import pandas as pd
from config import CUENTAS, TYPES_EDO_CTA
from cves import asign_cve
from utils import get_current_month_range
from conc import conciliar

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
# Agregamos los widgets para arrastrar los archivos
for banco, cuentas in CUENTAS.items():
    for cuenta in cuentas:
        uploaded_files[(banco,cuenta)] = cols[(banco,cuenta)].file_uploader(
            f"Cuenta {cuenta}",
            type=TYPES_EDO_CTA[banco],
            accept_multiple_files=False,
        )
        if uploaded_files[(banco,cuenta)]:
            dfs_edo_cta[(banco,cuenta)] = asign_cve(uploaded_files[(banco,cuenta)],banco,cuenta)
            cols[(banco,cuenta)].markdown('Procesado correctamente.')

st.header("Arrastra el reporte de caja de SAP")
uploaded_files['sap'] = st.file_uploader(
    'Caja Partidas Individuales',
    type=['csv'],
    accept_multiple_files=False
)
if uploaded_files['sap']:
    sap_caja = pd.read_csv(uploaded_files['sap'], encoding='utf-8', header=12)
    st.write(sap_caja.head())
    st.markdown('Procesado correctamente.')

# Agregamos selector de periodo a conciliar
periodo = st.date_input('Periodo a conciliar',get_current_month_range(),format='DD.MM.YYYY')
# Validamos que se haya ingresado al menos un estado de cuenta, el reporte de SAP y el periodo a conciliar
if len(dfs_edo_cta)>=1 and uploaded_files['sap'] and periodo:
    st.button('Conciliar',on_click=conciliar,args=[pd.concat(dfs_edo_cta.values()), sap_caja, periodo])