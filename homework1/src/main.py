import os
import json
from emulator import Emulator
import tkinter as tk
from tkinter import scrolledtext

def load_config():
    with open("C:/Users/Ultre/Documents/hw_1/other/config.json") as config_file:
        return json.load(config_file)

def run_gui(config):
    root = tk.Tk()
    root.title(f"Shell Emulator - {config['username']}")

    # Текстовое поле для вывода и ввода команд
    terminal_output = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20, width=80)
    terminal_output.grid(row=0, column=0, padx=10, pady=10)
    terminal_output.configure(state=tk.NORMAL)

    # Эмулятор
    emulator = Emulator(config, terminal_output)

    # Формируем начальное приглашение
    def get_prompt():
        return f"{config['username']}@shell:{emulator.current_dir}"

    # Печать начального приглашения
    def print_prompt():
        terminal_output.insert(tk.END, f"{get_prompt()} ")
        terminal_output.mark_set("insert", "end")
        terminal_output.see(tk.END)

    print_prompt()

    def on_enter_pressed(event):
        # Получаем текущую строку (приглашение и команда)
        current_line = terminal_output.get("insert linestart", "insert lineend").strip()

        # Разделяем на приглашение и команду
        prompt = get_prompt()
        if current_line.startswith(prompt):
            command = current_line[len(prompt):].strip()
        else:
            command = ""

        # Если команда пуста (только пробелы или ничего), просто выводим новое приглашение
        if not command:
            terminal_output.insert(tk.END, "\n")
            print_prompt()
            return "break"

        # Выполняем команду через эмулятор
        terminal_output.insert(tk.END, "\n")  # Переход на новую строку для вывода результата
        emulator.execute_command(command)

        # Печатаем новое приглашение
        print_prompt()

        # Останавливаем перенос на новую строку
        return "break"

    # Привязка клавиши Enter для выполнения команд
    terminal_output.bind("<Return>", on_enter_pressed)

    # Устанавливаем фокус на текстовое поле
    terminal_output.focus()

    root.mainloop()

if __name__ == "__main__":
    config = load_config()
    run_gui(config)
