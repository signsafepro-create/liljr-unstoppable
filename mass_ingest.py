import os
import json
import sqlite3
import time

DB_FILE = "C:\\Users\\wjhmo\\liljr-unstoppable\\liljr_neural_matrix.db"
# THE TARGETS: Tell Jarvis exactly where to look for the 1.88M files
TARGET_PATHS = [r"C:\Users\wjhmo\LILJR-DEEP", r"C:\Users\wjhmo\liljr-unstoppable", r"C:\Users\wjhmo\Desktop"]

def mass_ingestion():
    print("🧠 STARTING MASS ASSIMILATION...")
    conn = sqlite3.connect(DB_FILE)
    processed = 0
    for path in TARGET_PATHS:
        if not os.path.exists(path): continue
        for root, dirs, files in os.walk(path):
            if any(x in root for x in ["node_modules", ".git", "AppData"]): continue
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    conn.execute("INSERT OR REPLACE INTO neural_vault (file_path, extension, content, weight) VALUES (?, ?, ?, ?)", 
                                 (full_path, os.path.splitext(file)[1], content, 1.0))
                    processed += 1
                    if processed % 500 == 0: 
                        conn.commit()
                        print(f"  Assimulated {processed} files...")
                except: continue
    conn.commit()
    conn.close()
    print(f"✅ SUCCESS: {processed} files are now part of the Lil.Jr 2.0 Brain.")

if __name__ == "__main__":
    mass_ingestion()
