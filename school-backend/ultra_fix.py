import psycopg2

def fix():
    databases = ['sms_central_db', 'sunrise_db']
    # Specific columns that are known to be missing
    fixes = [
        ('teachers_teacher', 'user_id', 'bigint'),
        ('teachers_teacher', 'school_id', 'bigint'),
        ('academics_librarybook', 'school_id', 'bigint'),
        # Add others if needed
    ]
    
    # Also add school_id to all tables just in case my previous simple_fix missed some
    tables = ["academics_classroom", "academics_subject", "academics_timetable", "academics_exam", "academics_examresult", "academics_librarybook", "academics_transportroute", "academics_teacherassignment", "academics_schoolevent", "students_student", "students_parent", "students_studentdocument", "teachers_teacher", "teachers_attendance", "finance_feetype", "finance_feestructure", "finance_feepayment"]

    for db in databases:
        print(f"Connecting to {db}...")
        try:
            # Use TCP to avoid hung socket
            conn = psycopg2.connect(f"dbname={db} user=satyam password=satyam host=127.0.0.1", connect_timeout=3)
            conn.autocommit = True
            cur = conn.cursor()
            
            for table, col, col_type in fixes:
                print(f"Checking {table}.{col} in {db}...")
                try:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type};")
                except Exception as e:
                    print(f"Error on {table}.{col} in {db}: {e}")
            
            for table in tables:
                print(f"Ensuring school_id in {table} ({db})...")
                try:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS school_id bigint;")
                except Exception as e:
                    # Table might not exist in this DB, which is fine
                    pass

            cur.close()
            conn.close()
            print(f"Done with {db}")
        except Exception as e:
            print(f"Connection failed for {db}: {e}")

if __name__ == '__main__':
    fix()
