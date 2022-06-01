#!/bin/sh


if echo "$PYTHON" | grep python ; then
    echo $PYTHON
    python=$PYTHON
else
    python="python3"
fi

echo $python
cd database_server

$python -m uvicorn main:app --host $DATABASE_HOST --port $DATABASE_PORT
