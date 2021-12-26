import pcclient


api = pcclient.API("nikita0607", "RoBo")


@api.main
async def main():
    await api.method.button.add("test", "Tap here!")  # Call method
    await api.method.computer.get_info()


api.run("http://192.168.1.137:8000/api")
