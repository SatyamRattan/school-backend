import psycopg2

def diag():
    try:
        conn = psycopg2.connect("dbname=sunrise_db user=satyam password=satyam", connect_timeout=3)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        existing = [t[0] for t in cur.fetchall()]
        print("Existing tables:", existing)
        
        # Candidate tables to check
        candidates = [
            "students_studentattendance", 
            "teachers_teacherattendance",
            "teachers_attendance",
            "teachers_staffleave",
            "teachers_payroll"
        ]
        
        for c in candidates:
            if c in existing:
                print(f"[OK] {c} exists")
            else:
                print(f"[MISSING] {c} is missing")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    diag()
