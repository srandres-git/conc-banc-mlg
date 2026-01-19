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
    header_found = False
    # buscamos la fila donde empiezan los datos (donde tenga la palabra "G/L Account" o "Cuenta de mayor")
    text_lines = uploaded_files['sap'].getvalue().decode('utf-8').splitlines()
    # contamos las líneas vacías para ajustar la búsqueda y considerar restarlas al final
    empty_lines = 0
    for i, line in enumerate(text_lines):
        if len(line)==0:
            empty_lines += 1
            continue
        if 'G/L Account' in line or 'Cuenta de mayor' in line:
            header_rows = i
            header_found = True
            break

    if not header_found:
        st.error('No se encontró la fila de encabezado en el archivo de SAP. Asegúrate de que el archivo es correcto.')
    else:
        try: 
            header_rows = header_rows - empty_lines
            sap_caja = pd.read_csv(uploaded_files['sap'], header=header_rows, dtype=str)
            sap_caja = format_sap_caja(sap_caja, periodo)
            st.success(f'Reporte SAP procesado correctamente: {len(sap_caja)} filas.')
        except KeyError as e:
            try:
                header_rows = header_rows + empty_lines
                sap_caja = pd.read_csv(uploaded_files['sap'], header=header_rows, dtype=str)
                sap_caja = format_sap_caja(sap_caja, periodo)
                st.success(f'Reporte SAP procesado correctamente: {len(sap_caja)} filas.')
            except KeyError as e:
                st.error(f'Error al leer los encabezados del archivo de SAP: {e}')
st.session_state['conc_button'] = st.container(key='conc_button')
st.session_state['conc_bancos'] = st.container(key='conc_bancos')
st.session_state['conc_sap'] = st.container(key='conc_sap')
# Validamos que se haya ingresado al menos un estado de cuenta, el reporte de SAP y el periodo a conciliar
if len(dfs_edo_cta)>=1 and uploaded_files['sap'] and periodo:
    with st.session_state['conc_button']:
        conciliacion = st.button('Conciliar',on_click=conciliar,args=[format_edo_cta(pd.concat(dfs_edo_cta.values(), ignore_index=True), periodo), sap_caja,periodo])

