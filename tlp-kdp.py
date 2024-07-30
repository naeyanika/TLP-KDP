import streamlit as st
import pandas as pd
import numpy as np
import io

# Define sum_list function
def sum_list(item):
    if isinstance(item, list):
        return sum(item)
    else:
        return item

st.title('Aplikasi Pengolahan TLP dan KDP')

# Function to format numbers
def format_no(no):
    try:
        if pd.notna(no):
            return f'{int(no):02d}.'
        else:
            return ''
    except (ValueError, TypeError):
        return str(no)

def format_center(center):
    try:
        if pd.notna(center):
            return f'{int(center):03d}'
        else:
            return ''
    except (ValueError, TypeError):
        return str(center)

def format_kelompok(kelompok):
    try:
        if pd.notna(kelompok):
            return f'{int(kelompok):02d}'
        else:
            return ''
    except (ValueError, TypeError):
        return str(kelompok)

# File upload
uploaded_files = st.file_uploader("Unggah file CSV", accept_multiple_files=True)

if uploaded_files:
    # Read CSV files
    dfs = {}
    for file in uploaded_files:
        df = pd.read_csv(file, delimiter=';', low_memory=False)
        dfs[file.name] = df

    #Informasi "df1 = dbpinjaman, df2=tlp, df2=kdp"
    # Process DbPinjaman

    if 'DbPinjaman.csv' in dfs:
        df1 = dfs['DbPinjaman.csv']
        df1.columns = df1.columns.str.strip()
        
        temp_client_id = df1['Client ID'].copy()
        df1['Client ID'] = df1['Loan No.']
        df1['Loan No.'] = temp_client_id
        
        df1.columns = ['NO.', 'DOCUMENT NO.', 'ID ANGGOTA', 'DISBURSE', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS PINJAMAN'] + list(df1.columns[11:])
        
        df1['NO.'] = df1['NO.'].apply(format_no)
        df1['CENTER'] = df1['CENTER'].apply(format_center)
        df1['KELOMPOK'] = df1['KELOMPOK'].apply(format_kelompok)
        
        st.write("DbPinjaman setelah diproses:")
        st.write(df1)

    # Process tlp
    if 'TLP.csv' in dfs:
        df2 = dfs['TLP.csv']
        df2.columns = df2.columns.str.strip()
        
        df2['TRANS. DATE'] = pd.to_datetime(df2['TRANS. DATE'], format='%d/%m/%Y', errors='coerce')
        df2['ENTRY DATE'] = pd.to_datetime(df2['ENTRY DATE'], format='%d/%m/%Y', errors='coerce')
        
        st.write("TLP setelah diproses:")
        st.write(df2)

    # Process kdp
    if 'KDP.csv' in dfs:
        df3 = dfs['KDP.csv']
        df3.columns = df3.columns.str.strip()
        
        df3['TRANS. DATE'] = pd.to_datetime(df3['TRANS. DATE'], format='%d/%m/%Y', errors='coerce')
        df3['ENTRY DATE'] = pd.to_datetime(df3['ENTRY DATE'], format='%d/%m/%Y', errors='coerce')
    # Filter KAS/BANK
        df3_cleaned = df3.dropna(subset=['DESCRIPTION'])
        df4 = df3_cleaned[df3_cleaned['DESCRIPTION'].str.startswith('KAS/BANK')].copy()
        
        df4['TRANS. DATE'] = df4['TRANS. DATE'].apply(lambda x: x.strftime('%d/%m/%Y'))
        df4['ENTRY DATE'] = df4['ENTRY DATE'].apply(lambda x: x.strftime('%d/%m/%Y'))
        df4['DEBIT'] = df4['DEBIT'].apply(lambda x: f'Rp {float(x):,.0f}')
        df4['CREDIT'] = df4['CREDIT'].apply(lambda x: f'Rp {float(x):,.0f}')
        
        st.write("KDP Setelah Filter:")
        st.write(df4)


    

    if 'DbPinjaman.csv' in dfs:
            # Merge untuk TLP
            df2_merged = pd.merge(df2, df1[['DOCUMENT NO.', 'ID ANGGOTA', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS PINJAMAN']], on='DOCUMENT NO.', how='left')

            rename_dict = {
            'PINJAMAN MIKRO BISNIS': 'PINJAMAN MIKROBISNIS',
            }
            df2_merged['JENIS PINJAMAN'] = df2_merged['JENIS PINJAMAN'].replace(rename_dict)

            # Merge untuk KDP
            df4_merged = pd.merge(df4, df1[['DOCUMENT NO.', 'ID ANGGOTA', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS PINJAMAN']], on='DOCUMENT NO.', how='left')

            rename_dict = {
            'PINJAMAN MIKRO BISNIS': 'PINJAMAN MIKROBISNIS',
            }
            df4_merged['JENIS PINJAMAN'] = df4_merged['JENIS PINJAMAN'].replace(rename_dict)

            # Filter N/A untuk TLP
            TLP_na = df2_merged[pd.isna(df2_merged['NAMA'])]

            # Filter N/A untuk KDP
            KDP_na = df4_merged[pd.isna(df4_merged['NAMA'])]

            st.write("TLP:")
            st.write(df2_merged)
            
            st.write("TLP N/A:")
            st.write(TLP_na)

            st.write("KDP:")
            st.write(df4_merged)
            
            st.write("KDP N/A:")
            st.write(KDP_na)
    
            # PIVOT TLP
            def sum_lists(x):
                if isinstance(x, list):
                    return sum(sum_list(item) for item in x)
                elif isinstance(x, str):
                    try:
                        return int(x.replace('Rp ','').replace(',', ''))
                    except ValueError:
                        return 0
                elif isinstance(x, (int, float)):
                    return x
                else:
                    return 0

            df2_merged['TRANS. DATE'] = pd.to_datetime(df2_merged['TRANS. DATE'], format='%d/%m/%Y').dt.strftime('%d%m%Y')
            df2_merged['DUMMY'] = df2_merged['ID ANGGOTA'] + '' + df2_merged['TRANS. DATE']

            pivot_table2 = pd.pivot_table(df2_merged,
                                          values=['DEBIT', 'CREDIT'],
                                          index=['ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'TRANS. DATE'],
                                          columns='JENIS PINJAMAN',
                                          aggfunc={'DEBIT': list, 'CREDIT': list},
                                          fill_value=0)

            for col in pivot_table2.columns:
                pivot_table2[col] = pivot_table2[col].apply(sum_lists)

            pivot_table2.columns = [f'{col[0]}_{col[1]}' for col in pivot_table2.columns]
            pivot_table2.reset_index(inplace=True)

            pivot_table2['TRANS. DATE'] = pd.to_datetime(pivot_table2['TRANS. DATE'], format='%d%m%Y').dt.strftime('%d/%m/%Y')

            new_columns4 = [
                'DEBIT_PINJAMAN UMUM',
                'DEBIT_PINJAMAN RENOVASI RUMAH',
                'DEBIT_PINJAMAN SANITASI',
                'DEBIT_PINJAMAN ARTA',
                'DEBIT_PINJAMAN MIKROBISNIS',
                'DEBIT_PINJAMAN DT. PENDIDIKAN',
                'DEBIT_PINJAMAN PERTANIAN',
                'CREDIT_PINJAMAN UMUM',
                'CREDIT_PINJAMAN RENOVASI RUMAH',
                'CREDIT_PINJAMAN SANITASI',
                'CREDIT_PINJAMAN ARTA',
                'CREDIT_PINJAMAN MIKROBISNIS',
                'CREDIT_PINJAMAN DT. PENDIDIKAN',
                'CREDIT_PINJAMAN PERTANIAN'
            ]

            for col in new_columns4:
                if col not in pivot_table2.columns:
                    pivot_table2[col] = 0

            pivot_table4 = pivot_table2.copy()
            for col in pivot_table4.columns:
                if col not in ['ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'TRANS. DATE']:
                    pivot_table4[col] = pivot_table4[col].apply(lambda x: f'Rp {int(x):,}' if x != 0 else 0)

            st.write("Pivot Table TLP:")
            st.write(pivot_table4)
