import peer
import psycopg2

try:
	conn = psycopg2.connect("dbname=sample user=postgres")
except:
	print "Cannot connect to database"

cur = conn.cursor()

conn.commit()
cur.close()

try:
	conn.close()
except:
	print "Cannot close connection"