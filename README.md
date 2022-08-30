Веб сервер, предназначнный для отдачи комманд большому количеству компьютеров.

## Getting started

Для начала, клонируйте этот репозиторий на ваш сервер и скачайте зависимости

```shell
git clone https://github.com/nikita0607/PC-Controller.git
cd PC-Controller
```

### Для WINDOWS

```shell
```

3) Запустите сервер с БД с помощью uvicorn в папке `database_server`
```shell
uvicorn main:app --host YOUR_IP --port 8001
```

4) Запустите API сервер
```shell
uvicorn main:app --host YOUR_IP
```

## Что дальше?
Теперь сервер может принимать API запросы.
Для этого вы можете написать свой код с отправкой post-запросов.
Или использовать [асинхронную библиотеку](https://github.com/nikita0607/PC-Controller-py) для Python: