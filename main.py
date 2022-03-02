import pandas as pd
from datetime import date, datetime
import os
import shutil
import sys
import sqlite3 as sql

def extract_data():
  fileName = input("Ingrese la ruta del archivo en formato csv: ")
  print(f"Ha seleccionado el archivo '{fileName}'.\n")

  dtypes = {
    'fiscal_id': 'str',
    'first_name': 'str',
    'last_name': 'str',
    'gender': 'str',
    'fecha_nacimiento': 'str',
    'fecha_vencimiento': 'str',
    'deuda': 'int',
    'direccion': 'str',
    'altura': 'int',
    'peso': 'int',
    'correo': 'str',
    'estatus_contacto': 'str',
    'prioridad': 'float',
    'telefono': 'str'
  }
  parse_dates = ['fecha_nacimiento', 'fecha_vencimiento']
  print("Extrayendo información del archivo seleccionado...")

  try:
    df = pd.read_csv(fileName, sep=';', dtype=dtypes, parse_dates=parse_dates)
    print("Extracción de la información exitosa.\n")
  except:
    print(f"Error al extraer la información del archivo ubicado en '{fileName}', verifique que la ruta sea correcta\n"
          "y ejecute de nuevo el programa.")
    sys.exit(1)
    
  df = df.applymap(lambda value: value.upper() if type(value) == str else value)

  df["prioridad"] = df['prioridad'].astype(pd.Int64Dtype())
  df['prioridad'].fillna(value = 0, inplace = True)
  df.fillna(value = 'N/A', inplace = True)

  return df

def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def define_age_group(age):
  bins= [0, 20, 30, 40, 50, 60, 110]
  labels = [1, 2, 3, 4, 5, 6]
  age_group_df = pd.cut(age, bins=bins, labels=labels)
  return age_group_df

def transform_data(df):
  # Customers table
  age = df['fecha_nacimiento'].apply(calculate_age)
  customers = df.iloc[:, :8].copy()
  customers.insert(5, "age", age)
  age_group = define_age_group(customers['age'])
  customers.insert(6, "age_group", age_group)
  delinquency = (datetime.today() - customers['fecha_vencimiento']).dt.days
  customers.insert(8, "delinquency", delinquency)
  new_customers_names = {'fecha_nacimiento': 'birth_date', 'fecha_vencimiento': 'due_date', 'deuda': 'due_balance', 'direccion': 'address'}
  customers = customers.rename(columns=new_customers_names)

  # Emails table
  emails_cols = ['fiscal_id', 'correo', 'estatus_contacto', 'prioridad']
  emails = df[emails_cols].copy()
  new_emails_names = {'correo': 'email', 'estatus_contacto': 'status', 'prioridad': 'priority'}
  emails = emails.rename(columns=new_emails_names)

  # Phones table
  phones_cols = ['fiscal_id', 'telefono', 'estatus_contacto', 'prioridad']
  phones = df[phones_cols].copy()
  new_phones_names = {'telefono': 'phone', 'estatus_contacto': 'status', 'prioridad': 'priority'}
  phones = phones.rename(columns=new_phones_names)

  # Saving tables in Excel files
  if (os.path.isdir('output')):
    shutil.rmtree('output')
    os.mkdir('output')
  else: 
    os.mkdir('output')

  customers.to_excel('output/clientes.xlsx', index=False)
  emails.to_excel('output/emails.xlsx', index=False)
  phones.to_excel('output/phones.xlsx', index=False)

def load_data():
  print('Cargando información a la base de datos...')

  try:
    conn = sql.connect('database.db3')

    # Reading data from Excel saved files
    customers = pd.read_excel('output/clientes.xlsx')
    emails = pd.read_excel('output/emails.xlsx')
    phones = pd.read_excel('output/phones.xlsx', dtype={'phone': 'str'})
    
    # Loading tables into SQlite database
    customers.to_sql('customers', conn, index=False, if_exists='replace')
    emails.to_sql('emails', conn, index=False, if_exists='replace')
    phones.to_sql('phones', conn, index=False, if_exists='replace')

    print('\n¡Carga exitosa!')
  except:
    print('\n¡Error al cargar la información a la base de datos!')

if __name__ == '__main__':
  df = extract_data()
  transform_data(df)
  load_data()