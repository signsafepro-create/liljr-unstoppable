import sqlite3

db = r"C:\Users\wjhmo\liljr-unstoppable\liljr_neural_matrix.db"

conn = sqlite3.connect(db)

try:
    count = conn.execute("SELECT COUNT(*) FROM neural_vault").fetchone()[0]
    print("neural_vault rows:", count)

    print("sample files:")

    try:
        rows = conn.execute("""
            SELECT file_path
            FROM neural_vault
            ORDER BY ingested_at DESC
            LIMIT 10
        """).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute("""
            SELECT file_path
            FROM neural_vault
            LIMIT 10
        """).fetchall()

    for row in rows:
        print(" -", row[0])

except Exception as e:
    print("ERROR:", e)

finally:
    conn.close()
