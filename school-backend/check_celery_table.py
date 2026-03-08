import psycopg2
import os

def check():
    try:
        conn = psycopg2.connect("dbname=sms_central_db user=satyam password=satyam host=127.0.0.1", connect_timeout=3)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'django_celery_beat_clockedschedule';")
        res = cur.fetchone()
        print(f"Table exists in central DB: {res is not None}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check()
