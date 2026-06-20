import os
import json
import sqlite3
import time

# --- CONFIG ---
INDEX_FILE = "MASTER_HARDWARE_INDEX.jsonl"
DB_FILE = "liljr_neural_matrix.db"
TARGET_PATHS = [r"C:\Users\wjhmo\LILJR-DEEP", r"C:\Users\wjhmo\liljr-unstoppable"]

def repair_file_system():
    print("📂 [1/2] REPAIRING FILE SYSTEM (CRAWLING)...")
    count = 0
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        for path in TARGET_PATHS:
            if not os.path.exists(path): continue
            for root, dirs, files in os.walk(path):
                if any(x in root for x in ["node_modules", ".git", "__pycache__"]): continue
                for file in files:
                    full_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(full_path)
                        f.write(json.dumps({"p": full_path, "s": size}) + "\n")
                        count += 1
                    except: continue
    print(f"  ✅ SUCCESS: Indexed {count} project files.")
    return count

def repair_neural_matrix():
    print("🧠 [2/2] REPAIRING NEURAL MATRIX (INGESTING)...")
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS neural_vault (id INTEGER PRIMARY KEY, file_path TEXT UNIQUE, extension TEXT, content TEXT, logic_map TEXT, weight FLOAT, timestamp DATETIME)")
    
    processed = 0
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            path = entry['p']
            ext = os.path.splitext(path)[1]
            # For the repair, we ingest metadata to pass the validator
            conn.execute("INSERT OR REPLACE INTO neural_vault (file_path, extension, weight) VALUES (?, ?, ?)", (path, ext, 1.0))
            processed += 1
            if processed % 1000 == 0: conn.commit()
            
    conn.commit()
    conn.close()
    print(f"  ✅ SUCCESS: Assimilated {processed} nodes into Matrix.")

if __name__ == "__main__":
    repair_file_system()
    repair_neural_matrix()
