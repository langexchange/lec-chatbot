import psycopg


if __name__ == "__main__":
  with psycopg.connect("dbname=langgeneral user=langteam password=Aa1234 host=localhost port=5434") as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT * FROM users")
      
      for record in cur:
          print(record)