import unittest
from unittest.mock import MagicMock
import os
from emulator import Emulator

class TestEmulatorCommands(unittest.TestCase):

    def setUp(self):
        # Путь к виртуальной файловой системе (путь к директории virtual_fs на вашем ПК)
        self.config = {
            "username": "abyssoftime",
            "fs_image": "C:/Users/Ultre/Documents/hw_1/other/virtual_fs.tar",
            "startup_script": "C:/Users/Ultre/Documents/hw_1/other/startup.sh"
        }
        self.output_mock = MagicMock()
        self.emulator = Emulator(self.config, self.output_mock)
    
    # 1. Тесты для команды 'ls'
    def test_ls_directory_contents(self):
        # Проверяем вывод команды ls в директории dir1
        self.emulator.current_dir = os.path.join(self.emulator.virtual_fs, "dir1")
        self.emulator.ls()
        # Ожидаемый вывод: список файлов в каталоге dir1
        expected_output = "file1.txt\nfile2.txt\n"
        self.output_mock.insert.assert_called_with("end", expected_output)

    def test_ls_empty_directory(self):
        # Проверяем вывод команды ls в пустой директории dir3
        self.emulator.current_dir = os.path.join(self.emulator.virtual_fs, "dir3")
        self.emulator.ls()
        # Ожидаемый вывод: пустая строка
        self.output_mock.insert.assert_called_with("end", "file5.txt\n")


    # 2. Тесты для команды 'cd'
    
    def test_cd_to_existing_directory(self):
        # Переход в существующую директорию dir2
        self.emulator.current_dir = self.emulator.virtual_fs
        self.emulator.cd(['cd', 'dir2'])
        self.assertEqual(self.emulator.current_dir, os.path.join(self.emulator.virtual_fs, 'dir2'))

    def test_cd_to_non_existent_directory(self):
        # Переход в несуществующую директорию dir4
        self.emulator.current_dir = self.emulator.virtual_fs
        self.emulator.cd(['cd', 'dir4'])
        # Проверка, что выводит ошибку
        self.output_mock.insert.assert_any_call('end', 'cd: dir4: No such file or directory\n')

    # 3. Тесты для команды 'exit'
    
    def test_exit_shell(self):
        # Проверка выхода из оболочки
        self.emulator.exit_shell()
        self.output_mock.insert.assert_any_call('end', 'Exiting shell...\n')

    def test_exit_shell_with_message(self):
        # Проверка корректного завершения с сообщением
        self.emulator.exit_shell()
        self.output_mock.quit.assert_called_once()

    # 4. Тесты для команды 'du'
    
    def test_du_disk_usage(self):
        # Проверка подсчета дискового пространства для dir1
        self.emulator.current_dir = os.path.join(self.emulator.virtual_fs, 'dir1')
        self.emulator.du()
        # Проверка, что выводит общий размер
        self.output_mock.insert.assert_any_call('end', 'Total disk usage: 127 bytes\n')

    def test_du_disk_usage_in_subdirectories(self):
        # Проверка подсчета дискового пространства для dir2 (с файлами)
        self.emulator.current_dir = os.path.join(self.emulator.virtual_fs, 'dir2')
        self.emulator.du()
        # Проверка, что выводится общий размер для всех файлов
        self.output_mock.insert.assert_any_call('end', 'Total disk usage: 0 bytes\n')

    # 5. Тесты для команды 'tree'
    
    def test_tree_output(self):
        # Проверка вывода структуры дерева для текущего каталога (virtual_fs)
        self.emulator.current_dir = self.emulator.virtual_fs
        self.emulator.tree()
        # Проверка, что структура дерева начинается с виртуальной системы
        self.output_mock.insert.assert_any_call('end', 'virtual_fs\n')
    
    def test_tree_subdirectory_output(self):
        # Проверка вывода дерева для каталога dir2
        self.emulator.current_dir = os.path.join(self.emulator.virtual_fs, 'dir2')
        self.emulator.tree()
        # Проверка, что вывод дерева содержит файлы dir3
        self.output_mock.insert.assert_any_call('end', '  file4.txt\n')
    
    # 6. Тесты для команды 'clear'
    
    def test_clear_output(self):
        # Проверка очистки вывода после выполнения команды clear
        self.emulator.clear()
        self.output_mock.delete.assert_any_call(1.0, 'end')
    
    def test_clear_with_large_output(self):
        # Моделируем длинный вывод и очистку
        self.emulator.output_widget.insert('end', 'a' * 1000)  # Симулируем вывод большого текста
        self.emulator.clear()
        self.output_mock.delete.assert_any_call(1.0, 'end')

if __name__ == "__main__":
    unittest.main()
