cd database_server
python3 -m uvicorn main:app --host $DATABASE_HOST --port $DATABASE_PORT
