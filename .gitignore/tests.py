import sys
sys.path.append(r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Scripts\conc-banc-mlg")
path_sap = r"C:\Users\Andres Sanchez\Downloads\FINGLAU10_Q0001.csv"
path_bancos = r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Estados de cuenta\Julio\edos_cta_mlg_julio.xlsx"
output_folder = r"C:\Users\Andres Sanchez\OneDrive - Multilog Internacional S.A de C.V\Documents\Conciliación estados de cuenta bancarios\Julio"

def test_conciliar(path_bancos, path_sap, periodo):
    from concil.conc import conciliar, format_edo_cta, format_sap_caja
    import pandas as pd
    # Cargar los datos de prueba
    edo_cta = pd.read_excel(path_bancos)
    sap_caja = pd.read_csv(path_sap, encoding='utf-8', header=9)
    sap_caja = format_sap_caja(sap_caja, periodo)
    edo_cta = format_edo_cta(edo_cta, periodo)
    # Ejecutar la función de conciliación
    conciliar(edo_cta, sap_caja, periodo,
              output_bancos=output_folder + r"\conciliacion_bancos.xlsx",
              output_sap=output_folder + r"\conciliacion_sap.xlsx"
              )

if __name__ == "__main__":
    from datetime import date
    periodo = (date(2025, 7, 1), date(2025, 7, 31))
    test_conciliar(path_bancos, path_sap, periodo)