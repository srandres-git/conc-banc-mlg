import pandas as pd
import streamlit as st
from utils import excel_col_letter
from config import COLS_TO_KEEP_EDO_CTA, RENAME_COLUMNS, COLS_TO_KEEP_SAP

def export_bank(df: pd.DataFrame, output_file, bank, account):
    sheet_name = f"{bank}_{account}"
    with pd.ExcelWriter(output_file, engine='xlsxwriter', datetime_format='dd-mm-yyyy') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name, freeze_panes=(2, 0), startrow=1)

        workbook = writer.book
        # Asignamos color a la pestaña
        worksheet = writer.sheets[sheet_name]
        worksheet.set_tab_color('#C6EFCE')
        # formato comma style
        comma_format = workbook.add_format({'num_format': '#,##0.00'})
        # Formato encabezado
        header_format = workbook.add_format({'bold': True, 'bg_color': '#C6EFCE', 'border': 2, 'font_color': '#000000'})
        # Formato encabezado de columna "CLAVE"
        cve_format = workbook.add_format({'bold': True, 'bg_color': '#FFF2CC', 'border': 2, 'font_color': '#000000'})
        # subtotales de suma
        subtotal_sum_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFF2CC',
            'border': 2,
            'font_color': '#000000',
            'num_format': '#,##0.00'
        })
        for col_num, value in enumerate(df.columns):
            # escribimos los encabezados
            if value=='CLAVE':
                worksheet.write(1, col_num, value, cve_format)
                # subtotal para cuenta de movimientos
                # La fórmula CONTAR va de la fila 3 (índice 2) hasta la última fila
                last_row = len(df) + 2
                col_letter = excel_col_letter(col_num)
                formula = f'=SUBTOTAL(3, {col_letter}3:{col_letter}{last_row})'
                worksheet.write_formula(0, col_num, formula, subtotal_sum_format)

            else:
                worksheet.write(1, col_num, value, header_format)
                # subtotales (suma) para importes
                if value in ['CARGO', 'ABONO', 'IMPORTE']:
                    # La fórmula SUMA va de la fila 3 (índice 2) hasta la última fila
                    last_row = len(df) + 2
                    col_letter = excel_col_letter(col_num)
                    formula = f'=SUBTOTAL(9, {col_letter}3:{col_letter}{last_row})'
                    worksheet.write_formula(0, col_num, formula,subtotal_sum_format)

            # Ajusta el ancho de las columnas
            max_len = max(df[value].astype(str).map(len).max(), len(value))
            col_len = max_len + 2 if max_len < 30 else 30
            # Aplica formato comma style a columnas numéricas
            if pd.api.types.is_numeric_dtype(df[value]) and value not in ['Fecha de contabilización', 'FECHA', 'Diferencia fechas (días)', 'movimientos']:
                worksheet.set_column(col_num, col_num, col_len, comma_format)
            else:
                worksheet.set_column(col_num, col_num, col_len)

def export_bank_reconciliation(conciliacion_edo_cta_sap: pd.DataFrame, output_file: str,edo_cta_cols: list[str]):
    """
    Exporta el DataFrame de conciliación bancaria (bancos vs SAP) a un archivo Excel.
    """
    # seleccionamos las columnas que nos interesan para el reporte final
    conciliacion_edo_cta_sap = conciliacion_edo_cta_sap[COLS_TO_KEEP_EDO_CTA]
    # renombramos las columnas
    conciliacion_edo_cta_sap.rename(columns=RENAME_COLUMNS, inplace=True)
    # guardamos el resultado en un archivo Excel

    # 1. Conciliación completa
    df_full = conciliacion_edo_cta_sap.copy()


    # 2. Solo conciliados
    df_conciliados = df_full[(df_full['Conciliado por'].isin(['Clave', 'Importe y Fecha']))
                            & (df_full['Diferencia importes']==0)
                            & (df_full['Diferencia fechas (días)']==0)]

    # 3. Solo no conciliados
    df_no_conciliados = df_full[df_full['Conciliado por'] == 'No conciliado']

    # 4. Diferencias en importes 
    # ignoramos las despreciables: <1 MXN o <0.1 USD
    df_diff_importe = df_full[((df_full['Diferencia importes'].abs() >=1) & (df_full['MONEDA'] == 'MXN'))
                            | ((df_full['Diferencia importes'].abs() >=0.1) & (df_full['MONEDA'] == 'USD')) ]

    # 5. Diferencias en fechas
    df_diff_fecha = df_full[df_full['Diferencia fechas (días)'] > 0]

    # 6. Resumen por cuenta/cargo-abono
    resumen = df_full.groupby(['BANCO', 'CUENTA', 'CARGO/ABONO', 'Conciliado por']).agg(
        movimientos=('CLAVE', 'count'),
        importe_total=('IMPORTE', 'sum')
    ).reset_index()

    # 7. Totales por moneda/cargo-abono
    totales = df_full.groupby(['CARGO/ABONO','MONEDA', 'Conciliado por']).agg(
        movimientos=('CLAVE', 'count'),
        importe_total=('IMPORTE', 'sum')
    ).reset_index()

    # 8. Escribir a Excel con formato
    # determinamos el formato de encabezado según la columna
    def get_header_format(col_name):
        if col_name in edo_cta_cols:
            return header_format_bancos
        elif col_name in ['Diferencia importes', 'Diferencia fechas (días)', 'movimientos', 'importe_total', 'Conciliado por']:
            return header_format_summary
        else:
            return header_format_sap

    with pd.ExcelWriter(output_file, engine='xlsxwriter', datetime_format='dd-mm-yyyy') as writer:
        # Escribe cada pestaña
        df_full.to_excel(writer, sheet_name='Bancos vs SAP', index=False, freeze_panes=(2, 0), startrow=1)
        df_conciliados.to_excel(writer, sheet_name='Conciliados', index=False, freeze_panes=(2, 0), startrow=1)
        df_no_conciliados.to_excel(writer, sheet_name='No conciliados', index=False, freeze_panes=(2, 0), startrow=1)
        df_diff_importe.to_excel(writer, sheet_name='Diferencia importe', index=False, freeze_panes=(2, 0), startrow=1)
        df_diff_fecha.to_excel(writer, sheet_name='Diferencia fecha', index=False, freeze_panes=(2, 0), startrow=1)
        resumen.to_excel(writer, sheet_name='Resumen', index=False, freeze_panes=(2, 0), startrow=1)
        totales.to_excel(writer, sheet_name='Totales por moneda', index=False, freeze_panes=(2, 0), startrow=1)

        workbook = writer.book
        # Asigna colores a las pestañas
        writer.sheets['Bancos vs SAP'].set_tab_color('#BDD7EE' )    # azul claro
        writer.sheets['Conciliados'].set_tab_color('#A9D08E')               # verde
        writer.sheets['No conciliados'].set_tab_color('#FF5050' )           # rojo
        writer.sheets['Diferencia importe'].set_tab_color('#FFD966')        # amarillo
        writer.sheets['Diferencia fecha'].set_tab_color( '#F4B084')         # naranja
        writer.sheets['Resumen'].set_tab_color('#B4C6E7')                   # azul grisáceo
        writer.sheets['Totales por moneda'].set_tab_color('#B7DEE8')        # azul agua

        # Formato comma style
        comma_format = workbook.add_format({'num_format': '#,##0.00'})
        # Formato encabezado
        # para columnas del estado de cuenta, usamos un formato con fondo verde claro
        header_format_bancos = workbook.add_format({'bold': True, 'bg_color': '#C6EFCE', 'border': 2, 'font_color': '#000000'})
        # para columnas de SAP, usamos un formato con fondo azul claro
        header_format_sap = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 2, 'font_color': '#000000'})
        # para encabezados de conciliación, usamos un formato con fondo amarillo claro
        header_format_summary = workbook.add_format({'bold': True, 'bg_color': '#FFF2CC', 'border': 2, 'font_color': '#000000'})
        # subtotales de suma
        subtotal_sum_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFF2CC',
            'border': 2,
            'font_color': '#000000',
            'num_format': '#,##0.00'
        })


        for sheet in ['Bancos vs SAP', 'Conciliados', 'No conciliados', 'Diferencia importe', 'Diferencia fecha', 'Resumen', 'Totales por moneda']:
            worksheet = writer.sheets[sheet]
            # Determina columnas a formatear
            if sheet in ['Bancos vs SAP', 'Conciliados', 'No conciliados', 'Diferencia importe', 'Diferencia fecha']:
                df = df_full
            elif sheet == 'Resumen':
                df = resumen
            else:
                df = totales
            # Escribe encabezado
            for col_num, value in enumerate(df.columns):
                worksheet.write(1, col_num, value, get_header_format(value))
                # subtotales (suma) para importes
                if 'importe' in value.lower() or 'debe' in value.lower() or 'haber' in value.lower() or 'movimientos' in value.lower():
                    # La fórmula SUMA va de la fila 3 (índice 2) hasta la última fila
                    last_row = len(df) + 2
                    col_letter = excel_col_letter(col_num)
                    formula = f'=SUBTOTAL(9, {col_letter}3:{col_letter}{last_row})'
                    worksheet.write_formula(0, col_num, formula,subtotal_sum_format)
                # subtotales (conteo) para movimientos
                elif 'clave' in value.lower():
                    # La fórmula CONTAR va de la fila 3 (índice 2) hasta la última fila
                    last_row = len(df) + 2
                    col_letter = excel_col_letter(col_num)
                    formula = f'=SUBTOTAL(3, {col_letter}3:{col_letter}{last_row})'
                    worksheet.write_formula(0, col_num, formula, header_format_summary)
            
            # Ajusta el ancho de las columnas
                max_len = max(df[value].astype(str).map(len).max() if value in df.columns else 0, len(value))
                col_len = max_len + 2 if max_len < 30 else 30
                # Aplica formato comma style a columnas numéricas
                if pd.api.types.is_numeric_dtype(df[value]) and value not in ['Fecha de contabilización', 'FECHA', 'Diferencia fechas (días)', 'movimientos']:
                    worksheet.set_column(col_num, col_num, col_len, comma_format)
                else:
                    worksheet.set_column(col_num, col_num, col_len)

    # mostramos el resumen en pantalla
    with st.container(key='conc_bancos'):
        st.markdown("### Resumen de conciliación Bancos vs SAP")
        st.write(resumen)


def export_sap_reconciliation(conciliacion_sap_vs_edo: pd.DataFrame, output_file: str, sap_cols: list[str]):
    """
    Exporta el DataFrame de conciliación bancaria (SAP vs bancos) a un archivo Excel.
    """
    # --- Exportación a Excel: SAP vs Bancos ---

    # Selecciona columnas y renombra
    conciliacion_sap_vs_edo = conciliacion_sap_vs_edo[COLS_TO_KEEP_SAP]
    conciliacion_sap_vs_edo.rename(columns=RENAME_COLUMNS, inplace=True)

    # 1. Conciliación completa
    df_full_sap = conciliacion_sap_vs_edo.copy()

    # 2. Solo conciliados
    df_conciliados_sap = df_full_sap[
        (df_full_sap['Conciliado por'].isin(['Clave', 'Importe y Fecha'])) &
        (df_full_sap['Diferencia importes'] == 0) &
        (df_full_sap['Diferencia fechas (días)'] == 0)
    ]

    # 3. Solo no conciliados
    df_no_conciliados_sap = df_full_sap[df_full_sap['Conciliado por'] == 'No conciliado']

    # 4. Diferencias en importes
    # ignoramos diferencias despreciables de <1 MXN o <0.1 USD
    df_diff_importe_sap = df_full_sap[((df_full_sap['Diferencia importes'].abs() >= 1) & (df_full_sap['MONEDA']=='MXN'))
                                    | ((df_full_sap['Diferencia importes'].abs() >=0.1) & (df_full_sap['MONEDA']=='USD'))]

    # 5. Diferencias en fechas
    df_diff_fecha_sap = df_full_sap[df_full_sap['Diferencia fechas (días)'] > 0]

    # 6. Resumen por cuenta/cargo-abono
    resumen_sap = df_full_sap.groupby(['Banco', 'ID de cuenta', 'Cargo/Abono', 'Conciliado por']).agg(
        movimientos=('Clave de movimiento bancario', 'count'),
        importe_total=('Importe', 'sum')
    ).reset_index()

    # 7. Totales por moneda/cargo-abono
    totales_sap = df_full_sap.groupby(['Cargo/Abono', 'Moneda de transacción', 'Conciliado por']).agg(
        movimientos=('Clave de movimiento bancario', 'count'),
        importe_total=('Importe', 'sum')
    ).reset_index()

    def get_header_format_sap(col_name):
        if col_name in sap_cols or col_name in RENAME_COLUMNS.values():
            return header_format_sap
        elif col_name in ['Diferencia importes', 'Diferencia fechas (días)', 'movimientos', 'importe_total', 'Conciliado por']:
            return header_format_summary
        else:
            return header_format_bancos
        
    # 8. Escribir a Excel con formato
    with pd.ExcelWriter(output_file, engine='xlsxwriter', datetime_format='dd-mm-yyyy') as writer:
        # Escribe cada pestaña
        df_full_sap.to_excel(writer, sheet_name='SAP vs Bancos', index=False, freeze_panes=(2, 0), startrow=1)
        df_conciliados_sap.to_excel(writer, sheet_name='Conciliados', index=False, freeze_panes=(2, 0), startrow=1)
        df_no_conciliados_sap.to_excel(writer, sheet_name='No conciliados', index=False, freeze_panes=(2, 0), startrow=1)
        df_diff_importe_sap.to_excel(writer, sheet_name='Diferencia importe', index=False, freeze_panes=(2, 0), startrow=1)
        df_diff_fecha_sap.to_excel(writer, sheet_name='Diferencia fecha', index=False, freeze_panes=(2, 0), startrow=1)
        resumen_sap.to_excel(writer, sheet_name='Resumen', index=False, freeze_panes=(2, 0), startrow=1)
        totales_sap.to_excel(writer, sheet_name='Totales por moneda', index=False, freeze_panes=(2, 0), startrow=1)

        workbook = writer.book
        # Asigna colores a las pestañas
        writer.sheets['SAP vs Bancos'].set_tab_color('#BDD7EE')
        writer.sheets['Conciliados'].set_tab_color('#A9D08E')
        writer.sheets['No conciliados'].set_tab_color('#FF5050')
        writer.sheets['Diferencia importe'].set_tab_color('#FFD966')
        writer.sheets['Diferencia fecha'].set_tab_color('#F4B084')
        writer.sheets['Resumen'].set_tab_color('#B4C6E7')
        writer.sheets['Totales por moneda'].set_tab_color('#B7DEE8')

        # Formato comma style
        comma_format = workbook.add_format({'num_format': '#,##0.00'})
        # Formato encabezado
        # para columnas del estado de cuenta, usamos un formato con fondo verde claro
        header_format_bancos = workbook.add_format({'bold': True, 'bg_color': '#C6EFCE', 'border': 2, 'font_color': '#000000'})
        # para columnas de SAP, usamos un formato con fondo azul claro
        header_format_sap = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 2, 'font_color': '#000000'})
        # para encabezados de conciliación, usamos un formato con fondo amarillo claro
        header_format_summary = workbook.add_format({'bold': True, 'bg_color': '#FFF2CC', 'border': 2, 'font_color': '#000000'})
        # subtotales de suma
        subtotal_sum_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFF2CC',
            'border': 2,
            'font_color': '#000000',
            'num_format': '#,##0.00'
        })

        for sheet, df in [
            ('SAP vs Bancos', df_full_sap),
            ('Conciliados', df_conciliados_sap),
            ('No conciliados', df_no_conciliados_sap),
            ('Diferencia importe', df_diff_importe_sap),
            ('Diferencia fecha', df_diff_fecha_sap),
            ('Resumen', resumen_sap),
            ('Totales por moneda', totales_sap)
        ]:
            worksheet = writer.sheets[sheet]
            # Escribe encabezado
            for col_num, value in enumerate(df.columns):
                worksheet.write(1, col_num, value, get_header_format_sap(value))
                # Subtotales (suma) para importes
                if 'importe' in value.lower() or 'debe' in value.lower() or 'haber' in value.lower() or 'movimientos' in value.lower():
                    last_row = len(df) + 2
                    col_letter = excel_col_letter(col_num)
                    formula = f'=SUBTOTAL(9, {col_letter}3:{col_letter}{last_row})'
                    worksheet.write_formula(0, col_num, formula, subtotal_sum_format)
                # Subtotales (conteo) para movimientos
                elif 'clave' in value.lower():
                    last_row = len(df) + 2
                    col_letter = excel_col_letter(col_num)
                    formula = f'=SUBTOTAL(3, {col_letter}3:{col_letter}{last_row})'
                    worksheet.write_formula(0, col_num, formula, header_format_summary)

            # Ajusta el ancho de las columnas
                max_len = max(df[value].astype(str).map(len).max() if value in df.columns else 0, len(value))
                col_len = max_len + 2 if max_len < 30 else 30
                # Aplica formato comma style a columnas numéricas
                if pd.api.types.is_numeric_dtype(df[value]) and value not in ['Fecha', 'FECHA', 'Diferencia fechas (días)', 'movimientos']:
                    worksheet.set_column(col_num, col_num, col_len, comma_format)
                else:
                    worksheet.set_column(col_num, col_num, col_len)
    # mostramos el resumen en pantalla
    with st.container(key='conc_sap'):
        st.markdown("### Resumen de conciliación SAP vs Bancos")
        st.write(resumen_sap)