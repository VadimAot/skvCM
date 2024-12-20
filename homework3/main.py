import sys
import re
import logging

# Настройка логгера
logging.basicConfig(level=logging.DEBUG)

def process_input_to_toml():
    toml_lines = []  # Список для хранения итоговых строк в формате TOML
    line_number = 0  # Для отслеживания номера строки
    dictionary_pattern = r'^\$\[\s*(.*?)\s*\]$'  # Регулярное выражение для словарей
    name_pattern = r'^[a-zA-Z0-9]+$'  # Регулярное выражение для имен (буквы и цифры)
    number_pattern = r'^-?\d+(\.\d+)?$'  # Регулярное выражение для чисел (целые и вещественные)
    constant_declaration_pattern = r'^\(def\s+(\w+)\s+(.+?)\)$'  # Регулярное выражение для объявления константы
    constant_usage_pattern = r'\|(\w+)\|'  # Регулярное выражение для использования константы
    array_pattern = r'^([\w]+)\((.*)\)$'  # Регулярное выражение для массивов

    constants = {}  # Словарь для хранения констант
    in_dictionary = False  # Флаг для отслеживания режима "накопления" словаря
    dictionary_lines = []  # Для хранения строк словаря

    print("Введите строки конфигурации (введите -1 для завершения ввода):")
    input_lines = []
    for line in sys.stdin:
        line = line.strip()
        if line == "-1":  # Завершение ввода
            break
        input_lines.append(line)

    def parse_array(array_content):
        """Рекурсивный парсер массивов."""
        result = []
        nested = []
        nested_level = 0
        current_item = ""

        for char in array_content:
            if char == '(':
                nested_level += 1
                if nested_level == 1:
                    if current_item.strip():
                        result.append(current_item.strip())
                    current_item = "array("
                else:
                    current_item += char
            elif char == ')':
                nested_level -= 1
                current_item += char
                if nested_level == 0:
                    nested_result = parse_array(current_item[6:-1])  # Рекурсивный вызов для вложенного массива
                    nested.append(f"array = [{', '.join(nested_result)}]")  # Добавляем вложенные массивы
                    current_item = ""
            elif char == ',' and nested_level == 0:
                if current_item.strip():
                    result.append(current_item.strip())
                current_item = ""
            else:
                current_item += char

        if current_item.strip():
            result.append(current_item.strip())

        return result + nested

    def remove_unnecessary_array_prefix(array_list):
        """Удаляет ненужный префикс 'array' из результирующего списка."""
        return [item for item in array_list if item != 'array']

    for line in input_lines:
        line_number += 1

        if line.startswith('!'):
            continue  # Игнорируем строки с однострочными комментариями

        # Обработка объявления констант: (def имя значение)
        const_decl_match = re.match(constant_declaration_pattern, line)
        if const_decl_match:
            const_name = const_decl_match.group(1)
            const_value = const_decl_match.group(2)
            if not re.match(number_pattern, const_value) and not (const_value.startswith('"') and const_value.endswith('"')):
                logging.error(f"Syntax error on line {line_number}: Invalid constant value '{const_value}'.")
                sys.exit(1)
            constants[const_name] = const_value  # Сохраняем константу
            logging.debug(f"Constant declared: {const_name} = {const_value}")
            continue

        # Замена константных выражений |имя|
        def replace_constants(match):
            const_name = match.group(1)
            if const_name in constants:
                return constants[const_name]
            logging.error(f"Undefined constant '{const_name}' used on line {line_number}.")
            sys.exit(1)

        line = re.sub(constant_usage_pattern, replace_constants, line)

        # Обработка чисел
        if re.match(number_pattern, line):
            toml_lines.append(f'value{line_number} = {line}')  # Записываем число в формате TOML
            continue

        # Обработка строк, которые могут быть именами (буквы и цифры)
        name_match = re.match(name_pattern, line)
        if name_match:
            name = name_match.group(0)  # Получаем имя
            toml_lines.append(f'{name} = ""')  # Пример записи имени в TOML, если имя встречено
            continue

        # Обработка массивов: array(1, 2, array(3, 4))
        array_match = re.match(array_pattern, line)
        if array_match:
            array_name = array_match.group(1)  # Имя массива
            array_content = array_match.group(2)  # Содержимое массива
            try:
                parsed_array = parse_array(array_content)
                # Убираем ненужный префикс 'array'
                parsed_array = remove_unnecessary_array_prefix(parsed_array)
                toml_array = f'{array_name} = [{", ".join(parsed_array)}]'
                toml_lines.append(toml_array)
            except ValueError as e:
                logging.error(f"Syntax error on line {line_number}: {e}")
                sys.exit(1)
            continue

        # Обработка начала словаря
        if line.startswith('$['):
            if in_dictionary:
                logging.error(f"Syntax error on line {line_number}: Nested dictionaries are not allowed.")
                sys.exit(1)  # Завершаем выполнение программы с ошибкой
            in_dictionary = True
            dictionary_lines.append(line)
            continue

        # Обработка завершения словаря
        if in_dictionary:
            dictionary_lines.append(line)
            if line.endswith(']'):
                in_dictionary = False
                # Объединяем строки словаря в один блок
                dict_block = " ".join(dictionary_lines).strip()
                dictionary_lines = []  # Очищаем накопленные строки

                # Применяем регулярное выражение к словарю
                dict_match = re.match(dictionary_pattern, dict_block, re.DOTALL)
                if dict_match:
                    dict_body = dict_match.group(1).strip()  # Содержимое словаря
                    try:
                        # Преобразование тела словаря в формат TOML
                        entries = re.split(r',\s*(?![^(]*\))', dict_body)
                        toml_dict_entries = []
                        for entry in entries:
                            if ":" not in entry:
                                raise ValueError(f"Missing ':' in dictionary entry on line {line_number}.")
                            key, value = map(str.strip, entry.split(":", 1))
                            # Проверяем, является ли значение массивом
                            array_match = re.match(array_pattern, value)
                            if array_match:
                                array_content = array_match.group(2)
                                parsed_array = parse_array(array_content)
                                value = f'[{", ".join(parsed_array)}]'
                            # Проверяем, является ли значение числом
                            elif re.match(number_pattern, value):
                                value = value
                            # Проверяем, является ли значение строкой
                            elif value.startswith('"') and value.endswith('"'):
                                value = value
                            else:
                                raise ValueError(f"Invalid value '{value}' in dictionary entry.")
                            toml_dict_entries.append(f'{key} = {value}')
                        toml_dict = f'{{{", ".join(toml_dict_entries)}}}'
                        toml_lines.append(f'dictionary = {toml_dict}')
                    except ValueError as e:
                        logging.error(f"Syntax error on line {line_number}: {e}")
                        sys.exit(1)  # Завершаем выполнение программы с ошибкой
                else:
                    logging.error(f"Syntax error on line {line_number}: Invalid dictionary format.")
                    sys.exit(1)  # Завершаем выполнение программы с ошибкой
            continue

        # Если строка не совпадает ни с одним шаблоном, возможно, это ошибка
        if line and not in_dictionary:
            logging.error(f"Syntax error on line {line_number}: Unrecognized syntax.")
            sys.exit(1)

    # Если ошибок не было, записываем результат в файл TOML
    if toml_lines:
        with open("res_output.toml", "w") as f:
            f.write("\n".join(toml_lines))
        print("TOML file created successfully.")
    else:
        logging.error("No valid TOML data to write.")
        sys.exit(1)  # Завершаем выполнение программы, если нет данных для записи

if __name__ == "__main__":
    process_input_to_toml()
