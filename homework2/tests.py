import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import subprocess
from main import (
    run_maven_dependency_tree,
    parse_dependency_tree,
    generate_dot_file,
    generate_graph,
    get_project_name,
)

class TestMavenVisualizer(unittest.TestCase):

    @patch("subprocess.run")
    def test_run_maven_dependency_tree_success(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="[INFO] +- dependency:artifact:1.0", stderr="")
        result = run_maven_dependency_tree("/path/to/project")
        self.assertIn("[INFO] +- dependency:artifact:1.0", result)

    @patch("subprocess.run")
    def test_run_maven_dependency_tree_error(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=1, stdout="", stderr="Maven error")
        with self.assertRaises(Exception) as context:
            run_maven_dependency_tree("/path/to/project")
        self.assertIn("Ошибка Maven: Maven error", str(context.exception))

    @patch("subprocess.run")
    def test_run_maven_dependency_tree_file_not_found(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = FileNotFoundError()
        with self.assertRaises(Exception) as context:
            run_maven_dependency_tree("/path/to/project")
        self.assertIn("Maven не найден", str(context.exception))

    def test_parse_dependency_tree(self):
        output = """
        [INFO] +- group:artifact:jar:1.0
        [INFO] \- group:artifact:jar:2.0
        """
        dependencies = parse_dependency_tree(output)
        self.assertEqual(len(dependencies), 2)
        self.assertEqual(dependencies[0], ("", "artifact"))
        self.assertEqual(dependencies[1], ("", "artifact"))

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_dot_file(self, mock_file):
        dependencies = [("artifact1", "1.0"), ("artifact2", "2.0")]
        generate_dot_file(dependencies, "test.dot", "project")

        mock_file.assert_called_once_with("test.dot", "w")
        handle = mock_file()
        handle.write.assert_any_call("digraph dependencies {\n")
        handle.write.assert_any_call("    \"project\" -> \"1.0\";\n")
        handle.write.assert_any_call("    \"project\" -> \"2.0\";\n")
        handle.write.assert_any_call("}\n")

    @patch("subprocess.run")
    def test_generate_graph_success(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        generate_graph("test.dot", "output.png", "dot")
        mock_subprocess_run.assert_called_once_with(
            ["dot", "-Tpng", "test.dot", "-o", "output.png"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    @patch("subprocess.run")
    def test_generate_graph_error(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=1, stdout="", stderr="Graphviz error")
        with self.assertRaises(Exception) as context:
            generate_graph("test.dot", "output.png", "dot")
        self.assertIn("Ошибка Graphviz: Graphviz error", str(context.exception))

    @patch("os.path.exists")
    def test_get_project_name_success(self, mock_exists):
        mock_exists.return_value = True
        result = get_project_name("/path/to/project")
        self.assertEqual(result, "pom.xml")

    @patch("os.path.exists")
    def test_get_project_name_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(Exception) as context:
            get_project_name("/path/to/project")
        self.assertIn("Файл pom.xml не найден", str(context.exception))

if __name__ == "__main__":
    unittest.main()
