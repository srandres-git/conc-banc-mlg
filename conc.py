import pandas as pd
import numpy as np
import re
from config import DATE_FORMAT, COL_CLAVE_MOV, CATALOGO_BANCOS,CATALOGO_CUENTAS,CATALOGO_BANCOS_EDO_CTA,CATALOGO_CUENTAS_EDO_CTA, CUENTA_A_MONEDA, SAP_LANGUAGE, SAP_VALUES_ENG_SPAN, SAP_COLS_ENG_SPAN
from datetime import datetime,date
from utils import separar_texto_cabecera

def format_sap_caja(sap_caja: pd.DataFrame, periodo: tuple[date,date]) -> pd.DataFrame:
    """Formateo Reporte Caja SAP"""
    if SAP_LANGUAGE == 'en':
        # traducimos los valores del reporte de SAP al español
        sap_caja.replace(SAP_VALUES_ENG_SPAN, inplace=True)
        # renombramos las columnas del reporte de SAP
        sap_caja.rename(columns=SAP_COLS_ENG_SPAN, inplace=True)

    # extraemos todos los asientos contables de anulación distintos de #
    asientos_anulacion = sap_caja[sap_caja['Asiento contable de anulación'] != '#']["Asiento contable de anulación"].unique()
    print(f"Número de asientos contables de anulación distintos de #: {len(asientos_anulacion)}")
    # los movimientos anulados son aquellos que tienen un Asiento contable de compensación igual a alguno de los de anulación anteriores
    # los eliminamos de la tabla
    sap_caja = sap_caja[~sap_caja['Asiento contable de compensación'].isin(asientos_anulacion)]

    # dejamos solo los que tienen un Tipo de asiento contable igual a alguno de los siguientes:
    # Cobro
    # Desembolso
    # Transferencia de fondos
    sap_caja = sap_caja[sap_caja['Tipo de asiento contable'].isin([
        'Cobro',
        'Desembolso',
        'Transferencia de fondos',
    ])]

    print(f"Número de filas en sap_caja: {len(sap_caja)}")
    print(f'Tipos de asiento contable únicos en sap_caja: {sap_caja["Tipo de asiento contable"].unique()}')

    for x in ['debe','haber']:
        for moneda in ['moneda de empresa', 'moneda de transacción']:
            # convertimos las columnas de importe a numéricas, considerando que se recibe en formato "\d{1,3}(,\d{3})*(\.\d{2})? [A-Za-z]{3}"
            sap_caja[f'Importe en {x} en {moneda}'] = sap_caja[f'Importe en {x} en {moneda}'].astype(str).str.replace(r"[\$A-Za-z,\s]","",regex=True)
            sap_caja[f'Importe en {x} en {moneda}'] = pd.to_numeric(sap_caja[f'Importe en {x} en {moneda}'], errors='coerce').fillna(0)

    # Fecha de contabilización a datetime
    sap_caja['Fecha de contabilización'] = pd.to_datetime(sap_caja['Fecha de contabilización'],errors='raise', format=DATE_FORMAT)
    # dejamos solo los movimientos que están dentro del periodo a conciliar
    sap_caja = sap_caja[(sap_caja['Fecha de contabilización'].dt.date >= periodo[0]) & (sap_caja['Fecha de contabilización'].dt.date <= periodo[1])]
    # hay valores no convertibles a datetime?
    if sap_caja['Fecha de contabilización'].isnull().sum() > 0:
        print(f"Hay {sap_caja['Fecha de contabilización'].isnull().sum()} valores no convertibles a datetime en 'Fecha de contabilización'")    

    # cambiamos Asiento contable y Mi banco a string
    sap_caja['Asiento contable'] = sap_caja['Asiento contable'].astype(str).str.replace(r'\.0$', '', regex=True)
    sap_caja['Mi banco'] = sap_caja['Mi banco'].astype(str).str.replace(r'\.0','',regex=True)
    # cambiamos Cuenta de mayor a string
    sap_caja['Cuenta de mayor'] = sap_caja['Cuenta de mayor'].astype(str)
    # cambiamos Mi banco a string
    sap_caja['Mi banco'] = sap_caja['Mi banco'].astype(str)



    # agregamos columna que indica si es un cargo o un abono
    sap_caja['Cargo/Abono'] = np.where(
        sap_caja['Importe en debe en moneda de transacción'] > 0,
        'ABONO',
        'CARGO'
    )
    # agregamos columna de importe dependiendo de si es un cargo o un abono
    sap_caja['Importe'] = np.where(
        sap_caja['Cargo/Abono'] == 'ABONO',
        sap_caja['Importe en debe en moneda de transacción'],
        sap_caja['Importe en haber en moneda de transacción']
    )
    # conteo de cargos y abonos
    conteo_cargos_abonos = sap_caja['Cargo/Abono'].value_counts()
    print(f"Cargos: {conteo_cargos_abonos['CARGO']}, Abonos: {conteo_cargos_abonos['ABONO']}")

    # Extracción de clave, tipo de movimiento y texto de la transferencia a partir del texto de cabecera

    # extraemos la clave de movimiento bancario de la columna 'Texto de posición de asiento contable', 
    # así como posiblemente el tipo de movimiento y el nombre de la transferencia

    # si al separar el texto de la columna 'Texto de posición de asiento contable' por el separador hay 3 partes,
    # la primera es el tipo de movimiento, la segunda es la clave de movimiento bancario y la tercera es el nombre de la transferencia
    # si hay 2 partes, la primera es el tipo de movimiento y la segunda es la clave de movimiento bancario
    # si hay 1 parte, la clave de movimiento bancario es la misma que el texto completo
    # si hay 0 partes, todo es NaN
    # si hay más de 3 partes, se ignoran las partes adicionales


    # aplicamos la función a la columna 'Texto de posición de asiento contable'
    sap_caja[['Tipo de movimiento', 'Clave de movimiento bancario', 'Nombre de transferencia']] = sap_caja[COL_CLAVE_MOV].apply(separar_texto_cabecera).apply(pd.Series)
    sap_caja['Tipo de movimiento'] = sap_caja['Tipo de movimiento'].str.strip()
    sap_caja['Clave de movimiento bancario'] = sap_caja['Clave de movimiento bancario'].str.strip()
    # eliminamos los ceros a la izquierda de la clave de movimiento bancario
    sap_caja['Clave de movimiento bancario'] = sap_caja['Clave de movimiento bancario'].apply(lambda x: re.sub(r'^[0]+', '', x) if isinstance(x, str) else x)
    sap_caja['Nombre de transferencia'] = sap_caja['Nombre de transferencia'].str.strip()
    # convertimos la columna 'Tipo de movimiento' a mayúsculas
    sap_caja['Tipo de movimiento'] = sap_caja['Tipo de movimiento'].str.upper()


    # agrupamos movimientos de sap_caja que estén dentro de la misma cuenta, en la misma fecha,
    # con la misma clave de movimiento bancario (no vacía)
    # separamos las columnas de sap por tipo y función de agregación
    agg_sap = {
        col: 'sum' for col in sap_caja.columns if 'Importe' in col
    }
    agg_sap['Fecha de contabilización'] = 'first'  # preservamos la primera fecha de contabilización, puesto que es la misma para todos los movimientos de la misma clave
    agg_sap.update({
        col: lambda x: ', '.join([y if not y is None else '' for y in x.unique() ]) for col in sap_caja.columns if col not in agg_sap
    })
    # agrupamos por las columnas clave y aplicamos las funciones de agregación
    sap_caja_grouped = sap_caja[sap_caja['Clave de movimiento bancario']!='#'].groupby(
        ['ID de cuenta bancaria/gastos menores', 'Fecha de contabilización', 'Clave de movimiento bancario'],
        as_index=False
    ).agg(agg_sap)
    sap_caja_grouped = sap_caja_grouped[(sap_caja_grouped['Asiento contable'].str.contains(','))
                                        & (sap_caja_grouped['Cargo/Abono'] == 'CARGO')]
    # extraemos las claves de movimiento bancario que tienen más de un movimiento
    duplicated_keys = sap_caja_grouped['Clave de movimiento bancario']
    sap_caja_grouped
    # quitamos del original los que tienen clave de movimiento bancario duplicada
    # en su lugar concatenamos los de sap_caja_grouped
    sap_caja.drop(sap_caja[sap_caja['Clave de movimiento bancario'].isin(duplicated_keys)].index, inplace=True)
    sap_caja = pd.concat([sap_caja, sap_caja_grouped], ignore_index=True)
    print(sap_caja[sap_caja['Asiento contable'].str.contains(',')])
    return sap_caja

def format_edo_cta(edo_cta_cves: pd.DataFrame, periodo: tuple[date,date]) -> pd.DataFrame:
    """Formateo estados de cuenta"""
    edo_cta_cves['CLAVE'] = edo_cta_cves['CLAVE'].astype(str).str.strip()
    # eliminamos los ceros a la izquierda de la clave
    edo_cta_cves['CLAVE'] = edo_cta_cves['CLAVE'].apply(lambda x: re.sub(r'^[0]+', '', x) if isinstance(x, str) else x)

    # Convertimos la cuenta a string, tomando los últimos 3 caracteres (rellenar con ceros a la izquierda si es necesario)
    edo_cta_cves['CUENTA'] = edo_cta_cves['CUENTA'].astype(str).str.strip()
    edo_cta_cves['CUENTA'] = edo_cta_cves['CUENTA'].apply(lambda x: x[-3:].zfill(3))

    # convertimos columnas a numéricas
    edo_cta_cves['CARGO'] = pd.to_numeric(edo_cta_cves['CARGO'], errors='coerce').fillna(0)
    edo_cta_cves['ABONO'] = pd.to_numeric(edo_cta_cves['ABONO'], errors='coerce').fillna(0)
    edo_cta_cves['SALDO'] = pd.to_numeric(edo_cta_cves['SALDO'], errors='coerce').fillna(0)

    # las fechas deben ser convertidas a datetime y resolución solo al día
    edo_cta_cves['FECHA'] = pd.to_datetime(edo_cta_cves['FECHA'], errors='coerce').dt.normalize()
    # filtramos por el periodo a conciliar
    edo_cta_cves = edo_cta_cves[(edo_cta_cves['FECHA'].dt.date >= periodo[0]) & (edo_cta_cves['FECHA'].dt.date <= periodo[1])]
    # hay valores no convertibles a datetime?
    if edo_cta_cves['FECHA'].isnull().sum() > 0:
        print(f"Hay {edo_cta_cves['FECHA'].isnull().sum()} valores no convertibles a datetime en 'FECHA'")
    # asignamos la moneda
    edo_cta_cves['MONEDA'] = edo_cta_cves.apply(lambda row: CUENTA_A_MONEDA.get((row['BANCO'], row['CUENTA']), 'NA'), axis=1)

    # agregamos columna que indica si es cargo o abono
    edo_cta_cves['CARGO/ABONO'] = np.where(
        edo_cta_cves['CARGO'] > 0,
        'CARGO',
        'ABONO'
    )
    # agregamos columna de importe dependiendo de si es un cargo o un abono
    edo_cta_cves['IMPORTE'] = np.where(
        edo_cta_cves['CARGO/ABONO'] == 'CARGO',
        edo_cta_cves['CARGO'],
        edo_cta_cves['ABONO']
    )


def conciliar(edo_cta_cves: pd.DataFrame, sap_caja: pd.DataFrame,):   
    """Conciliación Bancos x SAP"""
    DIFF_RAN = 1
    conciliados = []
    # Paso 1: separamos los reportes por banco, cuenta y tipo de movimiento (CARGO/ABONO)
    for (banco,cuenta,tipo), edo_cta_group in edo_cta_cves.groupby(['BANCO', 'CUENTA', 'CARGO/ABONO']):
        sap_caja_group = sap_caja[(sap_caja['Unnamed: 3'] == CATALOGO_BANCOS_EDO_CTA[banco]) &
                                (sap_caja['ID de cuenta bancaria/gastos menores'] == CATALOGO_CUENTAS_EDO_CTA[banco][cuenta]) &
                                (sap_caja['Cargo/Abono'] == tipo)].copy()
        print(f"Banco: {banco}, Cuenta: {cuenta}, Tipo: {tipo}")
        edo_cta_group = edo_cta_group.copy()

        # Paso 2: Merge de los dataframes por clave
        merged = pd.merge(
            edo_cta_group,
            sap_caja_group,
            how='left',
            left_on='CLAVE',
            right_on='Clave de movimiento bancario',
            suffixes=('_edo_cta', '_sap'),
            indicator=True
        )

        # Paso 3: si hay más de un match por clave, quedarse con el de fecha más cercana

        # comparamos las fechas de los movimientos
        merged['Diferencia fechas (días)'] = (merged['Fecha de contabilización'] - merged['FECHA']).abs().dt.days
        # eliminar duplicados dejando el de fecha más cercana
        closest_match = merged.copy()
        closest_match = closest_match[closest_match['_merge'] == 'both']
        closest_match = closest_match.loc[
            closest_match.groupby(edo_cta_cves.columns.to_list())['Diferencia fechas (días)'].idxmin()
        ]
        # marcamos estos movimientos como conciliados por clave
        closest_match['Conciliado por'] = 'Clave'
        print(closest_match.index.size)
        # agregamos los movimientos conciliados a la lista
        conciliados.append(closest_match)
        # determinamos los movimientos que no se han conciliado por clave (auquellos de edo_cta_group cuyos datos no están en closest_match)
        no_conciliados = merged[merged['_merge'] == 'left_only'].copy()    
        no_conciliados['Conciliado por'] = 'No revisado'
        print(no_conciliados['_merge'].value_counts())  
        # determinamos los movimientos que no se han  conciliado del lado de SAP
        ids_conc = closest_match['Clave de movimiento bancario'].dropna().unique()
        no_conciliados_sap = sap_caja_group[~sap_caja_group['Clave de movimiento bancario'].isin(ids_conc)]
        
        # Paso 4: match por importe y fecha
        for i, row in no_conciliados.iterrows():
            # buscamos el movimiento en SAP que tenga la misma fecha y el importe más cercano dentro de los rangos
            match = no_conciliados_sap[
                ((no_conciliados_sap['Importe']-row['IMPORTE']).abs()<= DIFF_RAN) &
                (no_conciliados_sap['Fecha de contabilización'] == row['FECHA'])
            ]
            if not match.empty:
                # reordenamos por la diferencia
                match = match.sort_values(
                    by = 'Importe',
                    key = lambda x: (x-row['IMPORTE']).abs(),
                    ascending = True
                )
                # tomamos el primero, de menor diferencia
                match_row = match.iloc[0]
                # actualizamos la fila del estado de cuenta con los datos del movimiento de SAP
                for col in no_conciliados_sap.columns:
                    no_conciliados.at[i, col] = match_row[col]
                # marcamos este movimiento como conciliado por importe y fecha
                no_conciliados.at[i, 'Conciliado por'] = 'Importe y Fecha'
                # agregamos este movimiento a la lista de conciliados
                conciliados.append(no_conciliados.loc[[i]])
                # eliminamos el movimiento de SAP de la lista de no conciliados por el índice
                no_conciliados_sap = no_conciliados_sap[no_conciliados_sap.index != match_row.name]
                # no_conciliados_sap = no_conciliados_sap[no_conciliados_sap['ID de documento original'] != match_row['ID de documento original']]
            # si no hay match, lo dejamos como no conciliado
            else:
                # marcamos este movimiento como no conciliado
                no_conciliados.at[i, 'Conciliado por'] = 'No conciliado'

        # agregamos los movimientos no conciliados a la lista de conciliados
        conciliados.append(no_conciliados[no_conciliados['Conciliado por'] == 'No conciliado'])
        print('Vals de no conciliados:',no_conciliados.value_counts('Conciliado por'))
        
    # Paso 5: Conciliación final
    conciliacion_edo_cta_sap = pd.concat(conciliados, ignore_index=True)
    # volvemos a calcular las diferencias de importes y fechas
    conciliacion_edo_cta_sap['Diferencia importes'] = conciliacion_edo_cta_sap['IMPORTE']- conciliacion_edo_cta_sap['Importe']
    conciliacion_edo_cta_sap['Diferencia fechas (días)'] = (conciliacion_edo_cta_sap['Fecha de contabilización'] - conciliacion_edo_cta_sap['FECHA']).abs().dt.days
    # aquellas compensaciones (PCOMP) no conciliadas que tengan moneda MXN e importe menor a 1 se marcan como "No conciliado (compensación)"
    conciliacion_edo_cta_sap['Conciliado por'] = conciliacion_edo_cta_sap.apply(
        lambda x: 'No conciliado (compensación)' if x['MONEDA']=='MXN' 
        and x['IMPORTE']<1 
        and x['Conciliado por']=='No conciliado' 
        and ('PCOMP ' in x['CONCEPTO'] or 'COMPENSACION' in x['CONCEPTO'])    
        else x['Conciliado por'],
        axis=1
    )
    # aquellas compensaciones (PCOMP) no conciliadas que tengan moneda USD e importe menor a 0.1 se marcan como "No conciliado (compensación)"
    conciliacion_edo_cta_sap['Conciliado por'] = conciliacion_edo_cta_sap.apply(
        lambda x: 'No conciliado (compensación)' if x['MONEDA']=='USD' 
        and x['IMPORTE']<0.1
        and x['Conciliado por']=='No conciliado' 
        and ('PCOMP ' in x['CONCEPTO'] or 'COMPENSACION' in x['CONCEPTO'])    
        else x['Conciliado por'],
        axis=1
    )

    # verificar que el número de filas sea el esperado
    print(f"Número total de filas en la conciliación: {len(conciliacion_edo_cta_sap)}")
    print(f"Número de filas en estados de cuenta: {len(edo_cta_cves)}")
    conciliacion_edo_cta_sap.groupby('CARGO/ABONO')['Conciliado por'].value_counts()



    """Conciliación SAP x Bancos"""

    # Lista para ir acumulando resultados
    conciliados = []

    # Paso 1: separamos los reportes de SAP por banco, cuenta y tipo de movimiento
    for (bank_sap, cuenta_sap, tipo), sap_group in sap_caja.groupby(['Unnamed: 3', 'ID de cuenta bancaria/gastos menores', 'Cargo/Abono']):
        # Obtenemos el nombre y código del estado de cuenta a partir de los catálogos
        try: 
            banco_edo = CATALOGO_BANCOS[bank_sap]
        except KeyError:
            print(f"Error: el banco {bank_sap} no está en el catálogo de bancos de estados de cuenta")
            continue
        try:
            cuenta_edo = CATALOGO_CUENTAS[banco_edo][cuenta_sap]
        except KeyError:
            print(f"Error: la cuenta {cuenta_sap} no está en el catálogo de cuentas de estados de cuenta para el banco {bank_sap}")
            continue
        print(f"Banco: {banco_edo}, Cuenta: {cuenta_edo}, Tipo: {tipo}")
        sap_group = sap_group.copy()

        # Filtramos el DataFrame de edo_cta para emparejar solo dentro del mismo banco, cuenta y tipo
        edo_cta_group = edo_cta_cves[
            (edo_cta_cves['BANCO'] == banco_edo) &
            (edo_cta_cves['CUENTA'] == cuenta_edo) &
            (edo_cta_cves['CARGO/ABONO'] == tipo)
        ].copy()

        # Paso 2: Merge de los dataframes por clave de movimiento bancario
        merged = pd.merge(
            sap_group,
            edo_cta_group,
            how='left',
            left_on='Clave de movimiento bancario',
            right_on='CLAVE',
            suffixes=('_sap', '_edo'),
            indicator=True
        )

        # Paso 3: si hay más de un match por clave, quedarnos con el de fecha más cercana
        merged['Diferencia fechas (días)'] = (merged['Fecha de contabilización'] - merged['FECHA']).abs().dt.days
        both = merged[merged['_merge'] == 'both']
        idx_min = both.groupby(sap_caja.columns.to_list())['Diferencia fechas (días)'].idxmin()
        closest = merged.loc[idx_min].copy()
        closest['Conciliado por'] = 'Clave'
        conciliados.append(closest)

        # Movimientos de SAP sin conciliación por clave
        no_conc_sap = merged[merged['_merge'] == 'left_only'].copy()
        no_conc_sap['Conciliado por'] = 'No revisado'

        # Filtramos edos_cta restantes que no hayan sido ya conciliados por clave
        claves_conc = closest['CLAVE'].dropna().unique()
        edo_restantes = edo_cta_group[~edo_cta_group['CLAVE'].isin(claves_conc)]

        # Paso 4: match por importe y fecha
        for i, row in no_conc_sap.iterrows():
            posibles = edo_restantes[
                ((edo_restantes['IMPORTE'] - row['Importe']).abs()<= DIFF_RAN) &
                (edo_restantes['FECHA'] == row['Fecha de contabilización'])
            ]
            if not posibles.empty:
                # reordenamos por la diferencia
                posibles = posibles.sort_values(
                    by= 'IMPORTE',
                    key = lambda x: (x-row['Importe']).abs(),
                    ascending = True
                )
                # tomamos el de menor diferencia
                match = posibles.iloc[0]
                # Copiamos datos de edo_cta al registro de SAP
                for col in edo_restantes.columns:
                    no_conc_sap.at[i, col] = match[col]
                no_conc_sap.at[i, 'Conciliado por'] = 'Importe y Fecha'
                conciliados.append(no_conc_sap.loc[[i]])
                # Excluimos el movimiento conciliado de edo_restantes por su índice
                edo_restantes = edo_restantes[edo_restantes.index != match.name]
                # edo_restantes = edo_restantes[edo_restantes['CLAVE'] != match['CLAVE']]
            else:
                no_conc_sap.at[i, 'Conciliado por'] = 'No conciliado'

        # Agregamos los no conciliados finales
        conciliados.append(no_conc_sap[no_conc_sap['Conciliado por'] == 'No conciliado'])

    # Paso 5: Armado de la conciliación final
    conciliacion_sap_vs_edo = pd.concat(conciliados, ignore_index=True)
    conciliacion_sap_vs_edo['Diferencia importes'] = conciliacion_sap_vs_edo['Importe'] - conciliacion_sap_vs_edo['IMPORTE']
    conciliacion_sap_vs_edo['Diferencia fechas (días)'] = (
        conciliacion_sap_vs_edo['FECHA'] - conciliacion_sap_vs_edo['Fecha de contabilización']
    ).abs().dt.days

    # verificamos el número de filas
    print(f"Número total de filas en la conciliación: {len(conciliacion_sap_vs_edo)}")
    print(f"Número de filas en SAP: {len(sap_caja)}")

    return conciliacion_edo_cta_sap, conciliacion_sap_vs_edo
