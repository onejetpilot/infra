"""Clean Kafka messages and write valid rows to PostgreSQL."""
import json, logging, os, re
from datetime import datetime
import psycopg2
from confluent_kafka import Consumer

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
ACTIONS={"login","logout","view","click","purchase"}
EMAIL=re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def connect():
    return psycopg2.connect(host=os.getenv("KAFKA_TASK_DB_HOST","kafka-task-db"),port=os.getenv("KAFKA_TASK_DB_PORT","5432"),dbname=os.getenv("KAFKA_TASK_DB","kafka_task"),user=os.getenv("KAFKA_TASK_USER","kafka_user"),password=os.getenv("KAFKA_TASK_PASSWORD","kafka2026"))

def clean(row):
    name=" ".join(str(row.get("user_name") or "").split())
    if not name or len(name)>=100: return None
    name=" ".join(word.capitalize() for word in name.lower().split())
    email=str(row.get("email") or "").strip().lower()
    if not EMAIL.fullmatch(email): return None
    try: age=int(str(row.get("age")).strip())
    except (TypeError,ValueError): age=0
    age=age if 1<=age<=100 else 0
    action=str(row.get("site_action") or "").strip().lower()
    if action not in ACTIONS: return None
    try: return int(row["id"]),name,email,age,action,datetime.fromisoformat(str(row.get("event_date") or "").strip())
    except (KeyError,TypeError,ValueError): return None

def run():
    consumer=Consumer({"bootstrap.servers":os.getenv("KAFKA_BOOTSTRAP_SERVERS","kafka:29092"),"group.id":os.getenv("KAFKA_CONSUMER_GROUP","task_events_consumer_razhin"),"auto.offset.reset":"earliest","enable.auto.commit":False})
    consumer.subscribe([os.getenv("KAFKA_TOPIC","task_events_log_razhin")])
    loaded=rejected=0
    try:
        with connect() as conn, conn.cursor() as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS kafka_dev.events_log_razhin (id BIGINT PRIMARY KEY,user_name VARCHAR(100) NOT NULL,email VARCHAR(254) NOT NULL,age SMALLINT NOT NULL,site_action VARCHAR(20) NOT NULL,event_date TIMESTAMP NOT NULL,load_dttm TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            while True:
                message=consumer.poll(5)
                if message is None: break
                if message.error(): raise RuntimeError(message.error())
                event=clean(json.loads(message.value().decode("utf-8")))
                if event:
                    cursor.execute("INSERT INTO kafka_dev.events_log_razhin (id,user_name,email,age,site_action,event_date) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",event)
                    loaded+=cursor.rowcount
                else: rejected+=1
                conn.commit(); consumer.commit(message=message,asynchronous=False)
    finally: consumer.close()
    logging.info("Consumer finished: loaded=%s rejected=%s",loaded,rejected)

if __name__=="__main__": run()
