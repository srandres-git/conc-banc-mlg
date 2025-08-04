COLS_EDO_CTA = ['BANCO','CUENTA', 'FECHA', 'DESCRIPCIÓN', 'CONCEPTO', 'REFERENCIA', 'REFERENCIA BANCARIA', 'BENEFICIARIO',
                'DETALLE', 'CARGO', 'ABONO', 'SALDO', 'CLAVE', 'TIPO MOVIMIENTO']
ENCODINGS = ['latin-1', 'utf-8', 'ISO-8859-1']
CUENTAS = {
    'Banamex': ['828','829','434'],
    'Santander': ['383','357'],
    'HSBC': ['019','455'],
    'BBVA': ['389','844'],
    'Banorte': ['858'],
    'PNC': ['865']
}
# extensiones de archivo aceptadas para cada estado de cuenta
TYPES_EDO_CTA = {
    'Banamex':'csv',
    'Santander': 'csv',
    'HSBC': 'xlsx',
    'BBVA': 'txt',
    'Banorte': 'csv',
    'PNC': 'csv'
}

# nombre de la columna del reporte de caja que contiene la clave de movimiento bancario
COL_CLAVE_MOV = 'Texto de cabecera'
# caracter que separa la clave de movimiento bancario del resto del texto
SEPARADOR = '|'
# formato de fecha en el archivo de caja SAP
DATE_FORMAT = '%d.%m.%Y'

# Vinculamos las cuentas de SAP con las cuentas de los estados de cuenta
# {Banco: {cta_sap: cta_edo_cta}}
CATALOGO_CUENTAS = {
    'Banamex': {
        'MLGMXNBNX828 (MLG1000 )': '828',
        'MLGUSDBNX829 (MLG1000 )': '829',
        'MLGUSDBNX434 (MLG1000 )': '434',
    },
    'Santander': {
        'MLGMXNSANT383 (MLG1000 )': '383',
        'MLGUSDSANT357 (MLG1000 )': '357',
    },
    'HSBC': {
        'MLGMXNHSBC019 (MLG1000 )': '019',
        'MLGUSDHSBC455 (MLG1000 )': '455',
    },
    'BBVA': {
        'MLGMXNBBVA389 (MLG1000 )': '389',
        'MLGUSDBBVA844 (MLG1000 )': '844',
    },
    'PNC': {
        'MLGUSDPNCP865 (MLG1000 )': '865',
    },
    'Banorte': {
        'MLGMXNBANORTE858 (MLG1000 )': '858',
    }
    }
# separamos estas cuentas por banco y moneda
MONEDAS_CUENTAS = {
    banco : {
        moneda : [cta for cta in cuentas.keys() if cta.startswith(f'MLG{moneda}')]
        for moneda in ['MXN', 'USD']
    } for banco, cuentas in CATALOGO_CUENTAS.items()
}
# hacemos este catálogo con las cuentas de los estados de cuenta
MONEDAS_CUENTAS_EDO_CTA = {
    banco: {
        moneda: [CATALOGO_CUENTAS[banco][cta] for cta in MONEDAS_CUENTAS[banco][moneda]]
        for moneda in ['MXN', 'USD']}
    for banco in CATALOGO_CUENTAS.keys()
}
# mapeo de cuenta a moneda
CUENTA_A_MONEDA = {}
for banco, monedas in MONEDAS_CUENTAS_EDO_CTA.items():
    for moneda, cuentas in monedas.items():
        for cuenta in cuentas:
            CUENTA_A_MONEDA[(banco, cuenta)] = moneda

# {Banco: {cta_edo_cta: cta_sap}}
# hacemos el catalogo inverso para poder buscar la cuenta de sap a partir de la cuenta del edo de cuenta
CATALOGO_CUENTAS_EDO_CTA = {
    banco: {v: k for k, v in c.items()}
    for banco, c in CATALOGO_CUENTAS.items()
}
# Vinculamos los nombres de los bancos en SAP con los nombres de los bancos en los estados de cuenta
# {Banco sap: Banco edo_cta}
CATALOGO_BANCOS = {
    'Banco Nacional de México': 'Banamex',
    'Banco Santander': 'Santander',
    'HSBC México': 'HSBC',
    'BBVA Bancomer': 'BBVA',
    'PNC BANK': 'PNC',
    'BANORTE': 'Banorte',
}
# {Banco edo_cta: Banco sap}
# hacemos el catalogo inverso para poder buscar el banco de sap a partir del banco del edo de cuenta
CATALOGO_BANCOS_EDO_CTA = {
    v: k for k, v in CATALOGO_BANCOS.items()
}

RENAME_COLUMNS = {
    'Unnamed: 1': 'Nombre cuenta de mayor',
    'Mi banco': 'ID Banco',
    'Unnamed: 3': 'Banco',
    'ID de cuenta bancaria/gastos menores': 'Cuenta',
    'Fecha de contabilización': 'Fecha',
    'ID de cliente/proveedor de contrapartida': 'ID Cliente/Proveedor',
    'Unnamed: 13': 'Cliente/Proveedor',
    'Importe en debe en moneda de empresa': 'Debe MXN',
    'Importe en haber en moneda de empresa': 'Haber MXN',
    'Importe en debe en moneda de transacción': 'Debe',
    'Importe en haber en moneda de transacción': 'Haber',
}
# columnas que se preservan del merge_sap
COLS_TO_KEEP_SAP = [
    # columnas de SAP
    'Cuenta de mayor',
    'Unnamed: 1',
    'Mi banco',
    'Unnamed: 3',
    'ID de cuenta bancaria/gastos menores',
    'Fecha de contabilización',
    'Tipo de asiento contable',
    'Asiento contable',
    'Texto de cabecera',
    'ID de documento original',
    'ID de cliente/proveedor de contrapartida',
    'Unnamed: 13', 
    'Nombre Adicional II',
    'ID de documento original de referencia',
    'Moneda de transacción',
    'Tipo de movimiento',
    'Nombre de transferencia',
    
    # columnas de estado de cuenta e importes
    
    'BANCO',
    'CUENTA',
    'MONEDA',
    'FECHA',
    'DESCRIPCIÓN',
    'CONCEPTO',
    'REFERENCIA',
    'REFERENCIA BANCARIA',
    'DETALLE',
    'TIPO MOVIMIENTO',
    'CLAVE',
    'Clave de movimiento bancario',
    'CARGO/ABONO',
    'Cargo/Abono',
    'IMPORTE',
    'Importe',
    'Importe en haber en moneda de transacción',
    'Importe en haber en moneda de empresa',
    'Importe en debe en moneda de transacción',
    'Importe en debe en moneda de empresa',
    'SALDO',
    # 'Diferencia cargos',
    # 'Diferencia abonos',
    'Diferencia importes',
    'Diferencia fechas (días)',
    'Conciliado por',
]
# columnas que se preservan del merge_edo_cta
COLS_TO_KEEP_EDO_CTA = [
# columnas de estado de cuenta
    'BANCO',
    'CUENTA',
    'MONEDA',
    'FECHA',
    'DESCRIPCIÓN',
    'CONCEPTO',
    'REFERENCIA',
    'REFERENCIA BANCARIA',
    'DETALLE',
    'TIPO MOVIMIENTO',
# columnas de SAP e importes
    
    'Cuenta de mayor',
    'Unnamed: 1',
    'Mi banco',
    'Unnamed: 3',
    'ID de cuenta bancaria/gastos menores',
    'Fecha de contabilización',
    'Tipo de asiento contable',
    'Asiento contable',
    'Texto de cabecera',
    'ID de documento original',
    'ID de cliente/proveedor de contrapartida',
    'Unnamed: 13', 
    'Nombre Adicional II',
    'ID de documento original de referencia',
    'Moneda de transacción',
    'Tipo de movimiento',
    'Nombre de transferencia',    
    'CLAVE',
    'Clave de movimiento bancario',
    'CARGO/ABONO',
    'Cargo/Abono',    
    'IMPORTE',
    'Importe',
    'Importe en haber en moneda de transacción',
    'Importe en haber en moneda de empresa',
    'Importe en debe en moneda de transacción',
    'Importe en debe en moneda de empresa',
    'SALDO',
    # 'Diferencia cargos',
    # 'Diferencia abonos',
    'Diferencia importes',
    'Diferencia fechas (días)',
    'Conciliado por',
]
# Diccionario de traducción de columnas del reporte de SAP al español
SAP_COLS_ENG_SPAN = {
    'G/L Account': 'Cuenta de mayor',
    'My Bank': 'Mi banco',
    'Cash Location Type': 'Tipo de ubicación de caja',
    'Bank Account / Petty Cash ID': 'ID de cuenta bancaria/gastos menores',
    'Posting Date': 'Fecha de contabilización',
    'Journal Entry Type': 'Tipo de asiento contable',
    'Journal Entry': 'Asiento contable',
    'External Reference ID': 'ID de referencia externa',
    'Header Text': 'Texto de cabecera',
    'Source Document ID': 'ID de documento original',
    'Offset Customer / Supplier ID': 'ID de cliente/proveedor de contrapartida',
    'Aditional Name II': 'Nombre Adicional II',
    'Source Document External Reference': 'Referencia externa de documento original',
    'Journal Entry Item Text': 'Texto de posición de asiento contable',
    'Transaction Currency': 'Moneda de transacción',
    'Clearing Journal Entry': 'Asiento contable de compensación',
    'Source Document ID.1':'ID de documento original.1',
    'Reference Source Document ID': 'ID de documento original de referencia',
    'Reversal Journal Entry': 'Asiento contable de anulación',
    'Debit Amount Company Currency': 'Importe en debe en moneda de empresa',
    'Credit Amount Company Currency': 'Importe en haber en moneda de empresa',
    'Debit Amount Transaction Currency': 'Importe en debe en moneda de transacción',
    'Credit Amount Transaction Currency': 'Importe en haber en moneda de transacción',
}
# Diccionario de traducción de valores del reporte de SAP al español
SAP_VALUES_ENG_SPAN = {
    'Journal Entry Type': {
        'Cash Disbursement': 'Desembolso',
        'Cash Receipt': 'Cobro',
        'Cash Transfer': 'Transferencia de fondos',
    }
}
# Idioma en el que se encuentra el reporte de SAP
SAP_LANGUAGE = 'en'  # 'en' para inglés, 'es' para español