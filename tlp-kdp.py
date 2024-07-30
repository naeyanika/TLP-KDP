import streamlit as st
import pandas as pd
import numpy as np
import io

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
    if 'TLP.csv' in dfs:
        df3 = dfs['KDP.csv']
        df3.columns = df3.columns.str.strip()
        
        df3['TRANS. DATE'] = pd.to_datetime(df3['TRANS. DATE'], format='%d/%m/%Y', errors='coerce')
        df3['ENTRY DATE'] = pd.to_datetime(df3['ENTRY DATE'], format='%d/%m/%Y', errors='coerce')
        
        st.write("KDP setelah diproses:")
        st.write(df3)



    

    if 'DbPinjaman.csv' in dfs:
            # Merge untuk TLP
            df2_merged = pd.merge(df2, df1[['DOCUMENT NO.', 'ID ANGGOTA', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS PINJAMAN']], on='DOCUMENT NO.', how='left')

            rename_dict = {
            'PINJAMAN MIKRO BISNIS': 'PINJAMAN MIKROBISNIS',
            }
            df2_merged['JENIS PINJAMAN'] = df2_merged['JENIS PINJAMAN'].replace(rename_dict)

            # Merge untuk KDP
            df3_merged = pd.merge(df3, df1[['DOCUMENT NO.', 'ID ANGGOTA', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS PINJAMAN']], on='DOCUMENT NO.', how='left')

            rename_dict = {
            'PINJAMAN MIKRO BISNIS': 'PINJAMAN MIKROBISNIS',
            }
            df3_merged['JENIS PINJAMAN'] = df3_merged['JENIS PINJAMAN'].replace(rename_dict)

            # Filter N/A untuk pinjaman
            TLP_na = df2_merged[pd.isna(df2_merged['NAMA'])]

            # Filter N/A untuk pinjaman
            KDP_na = df3_merged[pd.isna(df3_merged['NAMA'])]

            st.write("TLP:")
            st.write(df2_merged)
            
            st.write("TLP N/A:")
            st.write(TLP_na)

            st.write("KDP:")
            st.write(df3_merged)
            
            st.write("KDP N/A:")
            st.write(KDP_na)
    
            # PIVOT TLP
            def sum_lists(x):
                if isinstance(x, list):
                    return sum(int(value.replace('Rp ', '').replace(',', '')) for value in x)
                return x

            df2_merged['TRANS. DATE'] = pd.to_datetime(df2_merged['TRANS. DATE'], format='%d/%m/%Y').dt.strftime('%d%m%Y')
            df2_merged['DUMMY'] = df2_merged['ID ANGGOTA'] + '' + df2_merged['TRANS. DATE']

            pivot_table2 = pd.pivot_table(df2_merged,
                                          values=['DEBIT', 'CREDIT'],
                                          index=['ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'TRANS. DATE'],
                                          columns='JENIS PINJAMAN',
                                          aggfunc={'DEBIT': list, 'CREDIT': list},
                                          fill_value=0)

            pivot_table2 = pivot_table2.applymap(sum_lists)
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

            pivot_table2['DEBIT_TOTAL'] = pivot_table2.filter(like='DEBIT').sum(axis=1)
            pivot_table2['CREDIT_TOTAL'] = pivot_table2.filter(like='CREDIT').sum(axis=1)

            rename_dict = {
                'KELOMPOK': 'KEL',
                'DEBIT_PINJAMAN ARTA': 'Db PRT',
                'DEBIT_PINJAMAN DT. PENDIDIKAN': 'Db DTP',
                'DEBIT_PINJAMAN MIKROBISNIS': 'Db PMB',
                'DEBIT_PINJAMAN SANITASI': 'Db PSA',
                'DEBIT_PINJAMAN UMUM': 'Db PU',
                'DEBIT_PINJAMAN RENOVASI RUMAH': 'Db PRR',
                'DEBIT_PINJAMAN PERTANIAN': 'Db PTN',
                'DEBIT_TOTAL': 'Db Total2',
                'CREDIT_PINJAMAN ARTA': 'Cr PRT',
                'CREDIT_PINJAMAN DT. PENDIDIKAN': 'Cr DTP',
                'CREDIT_PINJAMAN MIKROBISNIS': 'Cr PMB',
                'CREDIT_PINJAMAN SANITASI': 'Cr PSA',
                'CREDIT_PINJAMAN UMUM': 'Cr PU',
                'CREDIT_PINJAMAN RENOVASI RUMAH': 'Cr PRR',
                'CREDIT_PINJAMAN PERTANIAN': 'Cr PTN',
                'CREDIT_TOTAL': 'Cr Total2'
            }
            
            pivot_table2 = pivot_table2.rename(columns=rename_dict)
            
            desired_order = [
            'ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KEL', 'HARI', 'JAM', 'SL', 'TRANS. DATE',
            'Db PTN', 'Cr PTN', 'Db PRT', 'Cr PRT', 'Db DTP', 'Cr DTP', 'Db PMB', 'Cr PMB', 'Db PRR', 'Cr PRR',
            'Db PSA', 'Cr PSA', 'Db PU', 'Cr PU', 'Db Total2', 'Cr Total2'
            ]

            # Tambahkan kolom yang mungkin belum ada dalam DataFrame
            for col in desired_order:
                if col not in pivot_table2.columns:
                    pivot_table2[col] = 0

            pivot_table2 = pivot_table2[desired_order]
        
            st.write("Pivot Table TLP:")
            st.write(pivot_table2)


            # PIVOT KDP
            def sum_lists(x):
                if isinstance(x, list):
                    return sum(int(value.replace('Rp ', '').replace(',', '')) for value in x)
                return x

            df3_merged['TRANS. DATE'] = pd.to_datetime(df3_merged['TRANS. DATE'], format='%d/%m/%Y').dt.strftime('%d%m%Y')
            df3_merged['DUMMY'] = df3_merged['ID ANGGOTA'] + '' + df3_merged['TRANS. DATE']

            pivot_table2 = pd.pivot_table(df3_merged,
                                          values=['DEBIT', 'CREDIT'],
                                          index=['ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'TRANS. DATE'],
                                          columns='JENIS PINJAMAN',
                                          aggfunc={'DEBIT': list, 'CREDIT': list},
                                          fill_value=0)

            pivot_table3 = pivot_table3.applymap(sum_lists)
            pivot_table3.columns = [f'{col[0]}_{col[1]}' for col in pivot_table3.columns]
            pivot_table3.reset_index(inplace=True)
            pivot_table3['TRANS. DATE'] = pd.to_datetime(pivot_table2['TRANS. DATE'], format='%d%m%Y').dt.strftime('%d/%m/%Y')

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
                    pivot_table3[col] = 0

            pivot_table3['DEBIT_TOTAL'] = pivot_table3.filter(like='DEBIT').sum(axis=1)
            pivot_table3['CREDIT_TOTAL'] = pivot_table3.filter(like='CREDIT').sum(axis=1)

            rename_dict = {
                'KELOMPOK': 'KEL',
                'DEBIT_PINJAMAN ARTA': 'Db PRT',
                'DEBIT_PINJAMAN DT. PENDIDIKAN': 'Db DTP',
                'DEBIT_PINJAMAN MIKROBISNIS': 'Db PMB',
                'DEBIT_PINJAMAN SANITASI': 'Db PSA',
                'DEBIT_PINJAMAN UMUM': 'Db PU',
                'DEBIT_PINJAMAN RENOVASI RUMAH': 'Db PRR',
                'DEBIT_PINJAMAN PERTANIAN': 'Db PTN',
                'DEBIT_TOTAL': 'Db Total2',
                'CREDIT_PINJAMAN ARTA': 'Cr PRT',
                'CREDIT_PINJAMAN DT. PENDIDIKAN': 'Cr DTP',
                'CREDIT_PINJAMAN MIKROBISNIS': 'Cr PMB',
                'CREDIT_PINJAMAN SANITASI': 'Cr PSA',
                'CREDIT_PINJAMAN UMUM': 'Cr PU',
                'CREDIT_PINJAMAN RENOVASI RUMAH': 'Cr PRR',
                'CREDIT_PINJAMAN PERTANIAN': 'Cr PTN',
                'CREDIT_TOTAL': 'Cr Total2'
            }
            
            pivot_table3 = pivot_table3.rename(columns=rename_dict)
            
            desired_order = [
            'ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KEL', 'HARI', 'JAM', 'SL', 'TRANS. DATE',
            'Db PTN', 'Cr PTN', 'Db PRT', 'Cr PRT', 'Db DTP', 'Cr DTP', 'Db PMB', 'Cr PMB', 'Db PRR', 'Cr PRR',
            'Db PSA', 'Cr PSA', 'Db PU', 'Cr PU', 'Db Total2', 'Cr Total2'
            ]

            # Tambahkan kolom yang mungkin belum ada dalam DataFrame
            for col in desired_order:
                if col not in pivot_table2.columns:
                    pivot_table2[col] = 0

            pivot_table3 = pivot_table3[desired_order]
        
            st.write("Pivot Table KDP:")
            st.write(pivot_table3)
    
    
    # Download links for pivot tables
    for name, df in {
        'pivot_pinjaman.xlsx': pivot_table4,
        'pivot_simpanan.xlsx': pivot_table5,
        'pinjaman_na.xlsx': df_pinjaman_na,
        'simpanan_na.xlsx': df_simpanan_na
    }.items():
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        buffer.seek(0)
        st.download_button(
            label=f"Unduh {name}",
            data=buffer.getvalue(),
            file_name=name,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
