#!/bin/sh


if echo "$PYTHON" | grep python ; then
    echo $PYTHON
    python=$PYTHON
else
    python="python3"
fi

echo $python

cd api_server
$python -m uvicorn main:app --host $API_HOST --port $API_PORT
