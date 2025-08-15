import sys
sys.path.append(r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Scripts\conc-banc-mlg")
path_sap = r"C:\Users\Andres Sanchez\Downloads\FINGLAU10_Q0001.csv"
path_bancos = r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\edos_cta_mlg_julio.xlsx"
output_folder = r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Conciliación estados de cuenta bancarios\Julio"
paths_edo_cta = [
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\Banamex\claves_MLG_BNX_EdoCtaMN_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\Banamex\claves_MLG_BNX_EdoCtaUS_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\Banamex\claves_MLG_BNX_EdoCtaUS734_Ago25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\Banorte\claves_MLG_BTE_EdoCta_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\BBVA\claves_MLG_BBVA_EdoCtaMN_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\BBVA\claves_MLG_BBVA_EdoCtaUS_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\HSBC\claves_MLG_EdoCtaHsbcDLS_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\HSBC\claves_MLG_EdoCtaHsbcMN_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\PNC\claves_MLG_PNC_EdoCta_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\Santander\claves_MLG_ST_EdoCtaMN_Jul25.xlsx",
    r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\Santander\claves_MLG_ST_EdoCtaUS_Jul25.xlsx",

]
def test_conciliar(path_bancos, path_sap, periodo, concat = False,start_row=0):
    from concil.conc import conciliar, format_edo_cta, format_sap_caja
    import pandas as pd
    # Cargar los datos de prueba
    if concat:
        # Si concat es True, cargar y concatenar múltiples archivos de estados de cuenta
        # path_bancos es una lista de rutas de archivos
        edo_cta_list = [pd.read_excel(path,header=start_row) for path in path_bancos]
        edo_cta = pd.concat(edo_cta_list,ignore_index=True)
    else:
        # Si concat es False, cargar un solo archivo de estados de cuenta
        edo_cta = pd.read_excel(path_bancos, header=start_row)
    sap_caja = pd.read_csv(path_sap, encoding='utf-8', header=9)
    # Formatear los datos
    edo_cta = format_edo_cta(edo_cta, periodo)
    sap_caja = format_sap_caja(sap_caja, periodo)
    
    # Ejecutar la función de conciliación
    conciliar(edo_cta, sap_caja, periodo,
              output_bancos=output_folder + r"\conciliacion_bancos.xlsx",
              output_sap=output_folder + r"\conciliacion_sap.xlsx"
              )

if __name__ == "__main__":
    from datetime import date
    periodo = (date(2025, 7, 1), date(2025, 7, 31))
    test_conciliar(paths_edo_cta, path_sap, periodo, concat=True, start_row=1)