@ECHO off

python3 --version > tmpFile
SET /p pyversion= < tmpFile
DEL tmpFile

IF "%pyversion%"=="Python" (
    SET /p python="Set destination for python: "
) ELSE ( IF "%pyversion:~0,9%"=="Python 3." (
    SET python="python3"
) ELSE (
    SET /p python="Set destination for python: "
))


IF NOT EXIST env/ (
    ECHO Create virtual environment
    %python% -m venv env
)

IF NOT EXIST ./env/tmp.txt (
    ECHO tmp file >> ./env/tmp.txt
    ECHO Update activate

    ECHO "" >> "./env/Scripts/old_activate.bat"
    MORE "./env/Scripts/activate.bat" >> "./env/Scripts/old_activate.bat"

    ECHO set API_HOST=127.0.0.1 >> ./env/Scripts/activate.bat
    ECHO set API_PORT=8000 >> ./env/Scripts/activate.bat

    ECHO set DATABASE_HOST=127.0.0.1 >> ./env/Scripts/activate.bat
    ECHO set DATABASE_PORT=8001 >> ./env/Scripts/activate.bat
)

CALL "./env/Scripts/activate.bat"
python -m pip install -r requirements.txt
