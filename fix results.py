import csv
import os
import re

import pandas as pd

input_directory = os.path.join('.', 'src', 'data', 'results')
files = [f for f in os.listdir(input_directory) if re.match(r'^[a-zA-Z]{2}_.*\.csv$', f)]

for file in files:
    file_path = os.path.join(input_directory, file)
    filename = os.path.basename(file_path)
    with open(file_path, mode='r', newline='', encoding='utf-8') as infile, open(filename, mode='w', newline='',
                                                                                  encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Ler e escrever o cabeçalho
        header = next(reader)
        writer.writerow(header)

        for row in reader:
            # Verificar se a coluna 'assessment_datetime' contém 'desktop' ou 'mobile'
            if row[12] in ['desktop', 'mobile']:
                # Recortar o valor da coluna 'assessment_datetime'
                print(row[12])
                platform_value = row[12]
                row[12] = row[13]
                row[13] = row[14]
                row[14] = row[15]
                row[15] = row[16]
                row[16] = row[17]
                row[17] = row[18]
                row[18] = row[19]
                row[19] = platform_value
            writer.writerow(row)

