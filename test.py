# test.py
import os
import glob
import pandas as pd
import xml.etree.ElementTree as ET
from config import ARQ_COMPUTADORES, PASTA_BASE_RFB, ANO_IRPF, SUBPASTA_DADOS

def main():
    df = pd.read_excel(ARQ_COMPUTADORES)
    target_cpf = "00111600804"
    
    paths_to_check = []
    for _, row in df.iterrows():
        computador = str(row["Computador"]).strip() if "Computador" in df.columns and pd.notna(row["Computador"]) else ""
        caminho_custom = str(row["Caminho"]).strip() if "Caminho" in df.columns and pd.notna(row["Caminho"]) else ""
        
        if caminho_custom:
            base = caminho_custom
        else:
            base = rf"\\{computador}\C$\{PASTA_BASE_RFB}\IRPF{ANO_IRPF}"
            
        path = os.path.join(base, SUBPASTA_DADOS, target_cpf)
        paths_to_check.append((row["Nome"], path))
        
    print(f"Checking {len(paths_to_check)} paths for CPF {target_cpf}...")
    
    found = 0
    for name, path in paths_to_check:
        if os.path.exists(path):
            print(f"\n[FOUND] User/PC: {name} -> Path: {path}")
            xml_files = glob.glob(os.path.join(path, "*.xml"))
            for xml_file in xml_files:
                found += 1
                mtime = os.path.getmtime(xml_file)
                from datetime import datetime
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # Check contents
                try:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    classe_java = root.get("classeJava", "")
                    
                    # Get saldoImpostoPagar
                    saldos = []
                    for elem in root.iter():
                        for k, v in elem.attrib.items():
                            if k.lower() == "saldoimpostopagar":
                                saldos.append(f"{elem.tag.split('}')[-1]}:{k}={v}")
                                
                    print(f"  File: {os.path.basename(xml_file)}")
                    print(f"    Modified: {mtime_str}")
                    print(f"    classeJava: {classe_java}")
                    print(f"    Saldos found: {saldos}")
                except Exception as e:
                    print(f"  File: {os.path.basename(xml_file)} - Error parsing: {e}")
                    
    if found == 0:
        print("No XML files found for this CPF on any machine.")

if __name__ == "__main__":
    main()
