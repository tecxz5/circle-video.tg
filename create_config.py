import os

def create_config_file(token):
    """Создает файл config.py с указанным токеном."""
    config_file_path = "config.py"
    with open(config_file_path, "w") as f:
        f.write(f"TOKEN = '{token}'\n")
    print(f"Файл {config_file_path} успешно создан.")

if __name__ == "__main__":
    token = input("Введите токен вашего бота: ")
    create_config_file(token)
    os.remove("create_config.py")
    print("Скрипт удален.")