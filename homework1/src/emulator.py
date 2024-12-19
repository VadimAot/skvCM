import os
import tarfile

class Emulator:
    def __init__(self, config, output_widget):
        self.config = config
        self.output_widget = output_widget
        self.virtual_fs = self.load_virtual_fs(config['fs_image'])
        self.current_dir = self.virtual_fs  # Начальный путь — это путь к распакованной системе

    def load_virtual_fs(self, fs_image_path):
        # Распаковываем архив виртуальной файловой системы в каталог virtual_fs
        fs_dir = "virtual_fs"
        with tarfile.open(fs_image_path, "r") as tar:
            tar.extractall(path=fs_dir)
        return fs_dir  # Возвращаем путь к виртуальной файловой системе

    def execute_command(self, command):
        # Убираем пробелы в начале и конце строки
        command = command.strip()

        # Если строка пуста (введены только пробелы), выводим новое приглашение
        if not command:
            self.output_widget.insert("end", f"{self.config['username']}@shell:{self.current_dir} ")
            self.output_widget.mark_set("insert", "end")
            return

        args = command.split()

        if not args:
            return

        cmd = args[0]
        if cmd == "ls":
            self.ls()
        elif cmd == "cd":
            self.cd(args)
        elif cmd == "exit":
            self.exit_shell()
        elif cmd == "du":
            self.du()
        elif cmd == "tree":
            self.tree()
        elif cmd == "clear":
            self.clear()
        else:
            self.output_widget.insert("end", f"Command not found: {cmd}\n")


    def ls(self):
        try:
            files = os.listdir(self.current_dir)
            self.output_widget.insert("end", "\n".join(files) + "\n")
        except FileNotFoundError:
            self.output_widget.insert("end", "No such file or directory\n")

    def cd(self, args):
        if len(args) < 2:
            self.output_widget.insert("end", "cd: missing operand\n")
            return

        new_dir = args[1]

        if new_dir == "..":
            # Если нужно перейти в родительскую директорию
            parent_dir = os.path.dirname(self.current_dir.rstrip("/"))
            if not parent_dir.startswith(self.virtual_fs):
                # Не разрешаем выйти за пределы виртуальной файловой системы
                self.current_dir = self.virtual_fs
            else:
                self.current_dir = parent_dir
        else:
            # Переход в указанную директорию
            new_path = os.path.normpath(os.path.join(self.current_dir, new_dir))
            if os.path.isdir(new_path) and new_path.startswith(self.virtual_fs):
                self.current_dir = new_path
            else:
                self.output_widget.insert("end", f"cd: {new_dir}: No such file or directory\n")

    def exit_shell(self):
        self.output_widget.insert("end", "Exiting shell...\n")
        self.output_widget.quit()

    def du(self):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.current_dir):
            for filename in filenames:
                total_size += os.path.getsize(os.path.join(dirpath, filename))
        self.output_widget.insert("end", f"Total disk usage: {total_size} bytes\n")

    def tree(self):
        def print_tree(path, indent=""):
            # Печатаем текущий каталог или файл
            self.output_widget.insert("end", f"{indent}{os.path.basename(path)}\n")
            # Рекурсивно обрабатываем подкаталоги и файлы
            if os.path.isdir(path):
                for child in sorted(os.listdir(path)):  # Сортируем для предсказуемого вывода
                    print_tree(os.path.join(path, child), indent + "  ")

        # Вывод дерева начинается с текущего каталога
        self.output_widget.insert("end", f"{os.path.basename(self.current_dir)}\n")
        print_tree(self.current_dir)


    def clear(self):
        self.output_widget.delete(1.0, "end")
