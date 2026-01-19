import streamlit as st
import pandas as pd
from concil.config import CUENTAS, TYPES_EDO_CTA
from format_banc.cves import asign_cve
from concil.utils import get_current_month_range
from concil.conc import conciliar, format_sap_caja, format_edo_cta

st.title("Conciliación bancaria")

st.info("Arrastra los estados de cuenta")
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
            cols[(banco,cuenta)].success(f'Archivo cargado correctamente.')

st.info("Arrastra el reporte de caja de SAP")
uploaded_files['sap'] = st.file_uploader(
    'Caja Partidas Individuales',
    type=['csv'],
    accept_multiple_files=False
)

# Agregamos selector de periodo a conciliar
periodo = st.date_input('Periodo a conciliar',get_current_month_range(),format='DD.MM.YYYY')

if uploaded_files['sap']:
    header_rows = 9
    header_found = False
    # buscamos la fila donde empiezan los datos (donde tenga la palabra "G/L Account" o "Cuenta de mayor")
    text_lines = uploaded_files['sap'].getvalue().decode('utf-8').splitlines()
    if not 'G/L Account' in text_lines[header_rows] and not 'Cuenta de mayor' in text_lines[header_rows]:
        st.write('Buscando fila de encabezado...')
        for i, line in enumerate(text_lines):
            if 'G/L Account' in line or 'Cuenta de mayor' in line:
                header_rows = i
                header_found = True
                break
    else:
        header_found = True
    if not header_found:
        st.error('No se encontró la fila de encabezado en el archivo de SAP. Asegúrate de que el archivo es correcto.')
    else:
        st.write(f'Fila de encabezado encontrada en la fila {header_rows + 1}.')
        sap_caja = pd.read_csv(uploaded_files['sap'], encoding='utf-8', header=header_rows)
        st.write(f'{sap_caja.columns.tolist()}')
        sap_caja = format_sap_caja(sap_caja, periodo)
        st.success(f'Reporte SAP procesado correctamente: {len(sap_caja)} filas.')
st.session_state['conc_button'] = st.container(key='conc_button')
st.session_state['conc_bancos'] = st.container(key='conc_bancos')
st.session_state['conc_sap'] = st.container(key='conc_sap')
# Validamos que se haya ingresado al menos un estado de cuenta, el reporte de SAP y el periodo a conciliar
if len(dfs_edo_cta)>=1 and uploaded_files['sap'] and periodo:
    with st.session_state['conc_button']:
        conciliacion = st.button('Conciliar',on_click=conciliar,args=[format_edo_cta(pd.concat(dfs_edo_cta.values(), ignore_index=True), periodo), sap_caja,periodo])

