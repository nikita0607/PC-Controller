Веб сервер, предназначнный для отдачи комманд большому количеству компьютеров.

## Getting started

Для начала, клонируйте этот репозиторий на ваш сервер и скачайте зависимости

```shell
git clone https://github.com/nikita0607/PC-Controller.git
python3 -m pip install -r requirements.txt
```

2) Запустите его
```shell
python3 main.py
```

Первый запуск создаст файл config.json:
```json
{"ip": ""}
```

В поле ip введите локальный ip вашего сервера, например:
```json
{"ip": "127.0.0.1"}
```

3) Снова запустите его!

Если вы все сделали правильно, вы увидете:
```shell
$ python3 main.py
 * Serving Flask app 'main' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 471-689-556
```

Теперь вы можете зайти на сайт с вашего сервера по адресу: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Подключение

Чтобы компьютеры могли локально подключатся к вашему серверу, для начала укажите в config.json локальный ip, например:
```json
{"ip": "192.168.0.100"}
```

Чтобы подключать компьютеры к серверу, вам нужно использовать клиент-приложение.
Вы можете написать его сами.
Для этого вы можете воспользоваться [этой библиотекой]("https://github.com/nikita0607/PC-Controller-py") для Python
