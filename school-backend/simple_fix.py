import psycopg2

def fix():
    tables = ["academics_classroom", "academics_subject", "academics_timetable", "academics_exam", "academics_examresult", "academics_librarybook", "academics_transportroute", "academics_teacherassignment", "academics_schoolevent", "students_student", "students_parent", "students_studentdocument", "teachers_teacher", "teachers_attendance", "finance_feetype", "finance_feestructure", "finance_feepayment"]
    
    databases = ['sms_central_db', 'sunrise_db']
    
    for db in databases:
        print(f"--- Fixing database: {db} ---")
        try:
            conn = psycopg2.connect(f"dbname={db} user=satyam password=satyam host=127.0.0.1", connect_timeout=3)
            conn.autocommit = True
            cur = conn.cursor()
            for table in tables:
                print(f"Fixing {table} in {db}...")
                try:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS school_id bigint;")
                    if table == 'teachers_teacher':
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS user_id bigint;")
                except Exception as e:
                    print(f"Error on {table} in {db}: {e}")
            cur.close()
            conn.close()
            print(f"Finished {db}!")
        except Exception as e:
            print(f"Connection error on {db}: {e}")
    print("All tasks done!")

if __name__ == '__main__':
    fix()
