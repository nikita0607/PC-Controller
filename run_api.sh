cd api_server
$PYTHON_DESTI -m uvicorn main:app --host $API_HOST --port $API_PORT
