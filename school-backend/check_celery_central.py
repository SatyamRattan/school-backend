import psycopg2

def check_central():
    try:
        conn = psycopg2.connect("dbname=sms_central_db user=satyam password=satyam host=127.0.0.1", connect_timeout=3)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'django_celery_beat%';")
        tables = [t[0] for t in cur.fetchall()]
        print("Celery tables in central DB:", tables)
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_central()
