import argparse
import subprocess
import os

def run_maven_dependency_tree(project_path):
    """Запускает команду mvn dependency:tree для указанного проекта."""
    try:
        result = subprocess.run(
            ["mvn.cmd", "dependency:tree", "-Dverbose"],  # Используем флаг -Dverbose для вывода всех зависимостей
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Ошибка Maven: {result.stderr}")
        return result.stdout
    except FileNotFoundError:
        raise Exception("Maven не найден. Убедитесь, что он установлен и добавлен в PATH.")

def parse_dependency_tree(output):
    """Парсит вывод mvn dependency:tree и возвращает список зависимостей."""
    dependencies = []
    current_dep = None

    for line in output.splitlines():
        line = line.strip()
        
        # Ищем прямые зависимости
        if line.startswith("[INFO]") and ":" in line:
            parts = line.split()
            if len(parts) > 1 and (parts[1].startswith("+-") or parts[1].startswith("\\-") or parts[1].startswith("|-")):
                # Извлекаем название зависимости и её версию
                from_dep = parts[1][2:]  # Убираем "+-" или "\-" или "|-"
                to_dep = parts[-1].split(":")[1]  # Берем версию (например, 3.12.0)
                dependencies.append((from_dep, to_dep))
    
    return dependencies

def generate_dot_file(dependencies, output_file, project_name):
    """Создаёт файл DOT для визуализации зависимостей с улучшенным оформлением."""
    with open(output_file, "w") as f:
        f.write("digraph dependencies {\n")
        
        # Настройка общего стиля графа
        f.write('    node [shape=box, style=filled, fillcolor=lightyellow, fontname="Arial"];\n')
        f.write('    edge [fontname="Arial", color=black];\n')

        # Добавление зависимостей с направлением от главного прямоугольника
        for from_dep, to_dep in dependencies:
            f.write(f'    "{project_name}" -> "{to_dep}";\n')  # Зависимость от текущей зависимости

        f.write("}\n")
    print(f"Файл DOT создан: {output_file}")

def generate_graph(dot_file, output_image, dot_path):
    """Генерирует изображение из файла DOT с помощью Graphviz."""
    try:
        result = subprocess.run(
            [dot_path, "-Tpng", dot_file, "-o", output_image],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Ошибка Graphviz: {result.stderr}")
        print(f"Графическое изображение создано: {output_image}")
    except FileNotFoundError:
        raise Exception("Graphviz не найден. Убедитесь, что утилита dot доступна в PATH.")

def get_project_name(project_path):
    """Извлекает имя XML-файла из пути проекта (например, pom.xml)."""
    pom_file = os.path.join(project_path, "pom.xml")
    if os.path.exists(pom_file):
        return "pom.xml"
    else:
        raise Exception("Файл pom.xml не найден в указанной директории.")

def main():
    parser = argparse.ArgumentParser(description="Визуализация зависимостей Maven.")
    parser.add_argument("--project-path", required=True, help="Путь к Maven-проекту.")
    parser.add_argument("--dot-path", default="dot", help="Путь к утилите dot (Graphviz).")
    parser.add_argument("--output-image", default="dependencies.png", help="Имя выходного файла изображения.")
    parser.add_argument("--dot-file", default="dependencies.dot", help="Имя выходного файла DOT.")
    args = parser.parse_args()

    try:
        # Автоматическое получение имени XML файла
        project_name = get_project_name(args.project_path)

        print("Запуск анализа зависимостей...")
        maven_output = run_maven_dependency_tree(args.project_path)
        dependencies = parse_dependency_tree(maven_output)

        print("Генерация файла DOT...")
        generate_dot_file(dependencies, args.dot_file, project_name)

        print("Создание графического изображения...")
        generate_graph(args.dot_file, args.output_image, args.dot_path)

        print("Задача выполнена. Откройте изображение:", args.output_image)
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
