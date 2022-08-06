#!/bin/sh


if python3 --version ; then
    python="python3"
else
    echo "Set destination for python" ; read python
fi


if cd env ; then
    cd ..
else
    echo Create virtual environment
    $python -m venv env
    
    cp ./env/bin/activate ./env/bin/old_activate
    
    echo "export PYTHON_DESTI=$python" >> ./env/bin/activate

    echo "export API_HOST=127.0.0.1" >> ./env/bin/activate
    echo "export API_PORT=8000" >> ./env/bin/activate
    
    echo "export DATABASE_HOST=127.0.0.1" >> ./env/bin/activate
    echo "export DATABASE_PORT=8001" >> ./env/bin/activate

fi



. ./env/bin/activate
$python -m pip install -r requirements.txt
