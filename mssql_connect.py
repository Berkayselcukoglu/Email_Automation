## MSSQL Bağlantısı & Gerekli Kütüphaneler

from typing import Iterator, Union
import pandas as pd
from pandas import DataFrame
from sqlalchemy import create_engine, text
import urllib.parse
import platform

## Database toolkit olarak SQLAlchemy kullanıyorum, database driver olarak da pyodbc kullanıyorum.
# Verileri alacağımız ilk fonksiyon;

def get_data():
    print(f"İşletim sistemi: {platform.system()} {platform.version()}")
    
    server = '#Veritabanı sunucusu adresi(MSSQL)'
    database = '#Veritabanı adı'
    
    connection_options = [
        f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Connection Timeout=30;CharSet=UTF-8;',
        f'DRIVER={{SQL Server}};SERVER=.\\SQLEXPRESS;DATABASE={database};Trusted_Connection=yes;Connection Timeout=30;CharSet=UTF-8;',
    ]

    for i, conn_str in enumerate(connection_options):
        try:
            print(f"Bağlantı yöntemi {i + 1} deneniyor...")
            params = urllib.parse.quote_plus(conn_str)
            engine = create_engine(f'mssql+pyodbc:///?odbc_connect={params}')

            # Bağlantı testi
            with engine.connect() as connection:
                result = connection.execute(text("SELECT @@VERSION"))
                version = result.scalar()
                print(f"Bağlantı başarılı")
                return engine
        except Exception as e:
            print(f"Bağlantı yöntemi {i + 1} başarısız: {e}")

    raise Exception("Bağlantı Başarısız!")

# Select sorgularını çalıştırmak için kullanılan fonksiyon;

def execute_sql_query(query: str) -> Union[None, DataFrame, Iterator[DataFrame]]:
    try:
        engine = get_data()
        return pd.read_sql_query(query, engine)
    except Exception as e:
        print(f"SQL hata: {e}")
        print(f"Sorgu: {query}")
        print("Bağlantı bilgileri kontrol ediliyor...")
        try:
            with engine.connect() as connection:
                print("Bağlantı başarılı")
        except Exception as conn_err:
            print(f"Bağlantı hatası!: {conn_err}")
        return None

# Tek bir değer döndüren sorgular için kullanılan fonksiyon;

def execute_sql_query_scalar(query):
    try:
        engine = get_data()
        with engine.connect() as connection:
            result = connection.execute(text(query))
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        print(f"Hata: {e}")
        return None
    
# INSERT, UPDATE, DELETE gibi sorguları çalıştırmak için kullanılan fonksiyon;

def execute_sql_modification(query, params=None):
    try:
        engine = get_data()
        with engine.connect() as connection:
            connection.execute(text(query), params or {})
            connection.commit()
        print("Sorgu başarıyla çalıştırıldı.")
        return True
    except Exception as e:
        print(f"SQL işlem hatası!: {e}")
        return False

# Belirtilen tablonun tüm verilerini döndüren fonksiyon;

def sql_table_data(table_name):
    query = f"SELECT * FROM [{table_name}]"
    return execute_sql_query(query)
