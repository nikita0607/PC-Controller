CALL env/Scripts/activate.bat

CD api_server
python3 -m uvicorn main:app --host $API_HOST --port $API_PORT