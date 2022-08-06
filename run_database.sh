cd database_server
$PYTHON_DESTI -m uvicorn main:app --host $DATABASE_HOST --port $DATABASE_PORT
