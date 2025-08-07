import chardet
import pandas as pd
import re
from datetime import datetime, date
import calendar
from config import SEPARADOR

def separar_texto_cabecera(texto):
    partes = texto.split(SEPARADOR)
    if len(partes) >= 3:
        return partes[0], partes[1], partes[2]
    elif len(partes) == 2:
        return partes[0],  partes[1], '#'
    elif len(partes) == 1:
        # buscamos el patrón [4 dígitos]_[T o G][10 dígitos], donde los 4 dígitos son el tipo de movimiento
        # y los 10 dígitos son la clave de movimiento bancario
        match = re.match(r'(\d{4})_([TG]\d{10})', partes[0])
        if match:
            tipo_movimiento = match.group(1)
            clave_mov_bancario = match.group(2)
            return tipo_movimiento, clave_mov_bancario, '#' 
        # verificamos que se pueda extraer algún formato de clave de movimiento bancario:
        # [T o G][10 dígitos]
        # [TMLG, NPRO o REEM][6 dígitos]
        if re.match(r'^[TG]\d{10}$', partes[0]) or re.match(r'^(TMLG|NPRO|REEM)\d{6}$', partes[0]):
            return '#', partes[0], '#'
        # si no, este será el nombre de la transferencia         
        else:
            return '#', '#', partes[0]
    else:
        return '#', '#', '#'
    
def get_current_month_range()->tuple[date, date]:
    """Obtiene las fechas del primer y último día del mes actual"""
    # Current date
    today = date.today()
    # First day of current month
    first_day = today.replace(day=1)
    # Last day of current month
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    return first_day,last_day
    
def get_encoding(uploaded_file):
    content = uploaded_file.read()               # bytes
    # Detectar la codificación del archivo
    result = chardet.detect(content)
    # Obtener la codificación
    encoding = result['encoding']
    return encoding

def txt_to_df(uploaded_file)->pd.DataFrame:
    content = uploaded_file.read()               # bytes
    encoding = chardet.detect(content)['encoding']
    if encoding is None:
        print("No se pudo detectar la codificación del archivo.")
        encoding = "latin-1"
    text = content.decode(encoding)              # str
    data = text.splitlines()                    # lista de líneas

    data = [i.split('\t') for i in data]
    # eliminar el \n del final de cada linea
    data = [[i.replace('\n','') for i in j] for j in data]
    # pasar a dataframe
    df = pd.DataFrame(data, columns = data[0])
    # eliminar la primera fila
    df = df.drop(0)
    df = df.reset_index(drop=True)

    return df

def excel_col_letter(col_idx):
    """Convierte índice de columna (0-based) a letra de Excel (A, B, ..., Z, AA, AB, ...)"""
    letters = ''
    while col_idx >= 0:
        letters = chr(col_idx % 26 + 65) + letters
        col_idx = col_idx // 26 - 1
    return letters

def get_month(period: tuple[date, date]) -> str:
    """Obtiene el mes en formato 'MMYY' a partir de un periodo si el periodo abarca máximo un mes,
    de lo contrario devuelve 'MMYY-MMYY'"""
    start_date, end_date = period
    if start_date.month == end_date.month and start_date.year == end_date.year:
        return f"{start_date.month:02d}{start_date.year % 100:02d}"    
    else:
        return f"{start_date.month:02d}{start_date.year % 100:02d}-{end_date.month:02d}{end_date.year % 100:02d}"
    
def get_export_filename(prefix: str, period: tuple[date, date], extension='xlsx') -> str:
    """Genera un nombre de archivo para exportar, incluyendo el prefijo, el periodo en formato 'MMYY' y la fecha de hoy en formato 'DDMMYY'"""""
    month = get_month(period)
    today = date.today()
    return f"{prefix}_{month}_{today.strftime('%d%m%y')}.{extension}"