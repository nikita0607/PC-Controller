if python3 --version ; then
    python="python3"
else
    echo Set destination for python: ; read python

$python -m pip install virtualenv
$python -m venv env
