"""
Analizador de código fuente para extracción de características de seguridad.
Utiliza AST parsing para detectar patrones de riesgo en código Python.
"""

import ast
import os
import re
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class CodeFeatures:
    """Características extraídas del código para análisis de vulnerabilidades"""
    # Métricas básicas
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    
    # Complejidad
    num_functions: int = 0
    num_classes: int = 0
    max_function_complexity: int = 0
    avg_function_complexity: float = 0.0
    
    # Patrones de riesgo
    has_eval: bool = False
    has_exec: bool = False
    has_input_direct: bool = False
    has_sql_concat: bool = False
    has_pickle_load: bool = False
    has_yaml_unsafe: bool = False
    
    # Imports peligrosos
    uses_os_system: bool = False
    uses_subprocess_shell: bool = False
    uses_deprecated_libs: bool = False
    
    # Manejo de errores
    has_bare_except: bool = False
    exception_handling_ratio: float = 0.0
    
    # Seguridad web
    has_hardcoded_secrets: bool = False
    has_flask_debug: bool = False
    has_unsafe_deserialization: bool = False
    
    # Patrones de inyección
    has_format_string_vuln: bool = False
    has_command_injection_risk: bool = False
    has_path_traversal_risk: bool = False
    
    # Criptografía
    uses_weak_crypto: bool = False
    uses_hardcoded_key: bool = False


class CodeAnalyzer:
    """Analiza código Python para detectar patrones de vulnerabilidades"""
    
    DANGEROUS_FUNCTIONS = {'eval', 'exec', '__import__', 'compile'}
    DEPRECATED_MODULES = {'md5', 'sha', 'cgi', 'imp'}
    WEAK_CRYPTO = {'DES', 'RC4', 'MD5', 'SHA1'}
    
    SQL_PATTERNS = [
        r'execute\s*\([^)]*\+',
        r'execute\s*\([^)]*%',
        r'execute\s*\(f["\']',
    ]
    
    SECRET_PATTERNS = [
        r'password\s*=\s*["\'][^"\']{3,}',
        r'api[_-]?key\s*=\s*["\'][^"\']{10,}',
        r'secret\s*=\s*["\'][^"\']{10,}',
        r'token\s*=\s*["\'][^"\']{10,}',
    ]
    
    def __init__(self):
        self.features = CodeFeatures()
        self.function_complexities = []
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analiza un archivo Python y extrae características"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Análisis básico
            self._analyze_basic_metrics(content)
            
            # Análisis de patrones de texto
            self._analyze_text_patterns(content)
            
            # Análisis AST
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree)
            except SyntaxError:
                pass  # Archivo con errores de sintaxis
            
            # Calcular métricas derivadas
            self._calculate_derived_metrics()
            
            return {
                'file': filepath,
                'features': asdict(self.features)
            }
        except Exception as e:
            return {
                'file': filepath,
                'error': str(e),
                'features': asdict(CodeFeatures())
            }
    
    def _analyze_basic_metrics(self, content: str):
        """Analiza métricas básicas del código"""
        lines = content.split('\n')
        self.features.total_lines = len(lines)
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                self.features.code_lines += 1
            elif stripped.startswith('#'):
                self.features.comment_lines += 1
    
    def _analyze_text_patterns(self, content: str):
        """Analiza patrones de texto que indican riesgos"""
        content_lower = content.lower()
        
        # SQL injection patterns
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self.features.has_sql_concat = True
                break
        
        # Secrets hardcodeados
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self.features.has_hardcoded_secrets = True
                break
        
        # Flask debug
        if 'debug=true' in content_lower or 'debug = true' in content_lower:
            self.features.has_flask_debug = True
        
        # Format string vulnerabilities
        if re.search(r'%\s*\([^)]*\)\s*s', content):
            self.features.has_format_string_vuln = True
        
        # Path traversal
        if re.search(r'open\s*\([^)]*\+', content) or '../' in content:
            self.features.has_path_traversal_risk = True
    
    def _analyze_ast(self, tree: ast.AST):
        """Analiza el árbol de sintaxis abstracta"""
        for node in ast.walk(tree):
            # Contar funciones y clases
            if isinstance(node, ast.FunctionDef):
                self.features.num_functions += 1
                complexity = self._calculate_complexity(node)
                self.function_complexities.append(complexity)
            elif isinstance(node, ast.ClassDef):
                self.features.num_classes += 1
            
            # Detectar llamadas peligrosas
            elif isinstance(node, ast.Call):
                self._analyze_call(node)
            
            # Detectar imports peligrosos
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                self._analyze_import(node)
            
            # Detectar bare except
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.features.has_bare_except = True
    
    def _analyze_call(self, node: ast.Call):
        """Analiza llamadas a funciones para detectar patrones peligrosos"""
        func_name = self._get_call_name(node)
        
        if func_name in self.DANGEROUS_FUNCTIONS:
            if func_name == 'eval':
                self.features.has_eval = True
            elif func_name == 'exec':
                self.features.has_exec = True
        
        elif func_name == 'input' and not self._has_validation(node):
            self.features.has_input_direct = True
        
        elif func_name in ('pickle.load', 'pickle.loads', 'cPickle.load'):
            self.features.has_pickle_load = True
            self.features.has_unsafe_deserialization = True
        
        elif func_name in ('yaml.load', 'yaml.unsafe_load'):
            self.features.has_yaml_unsafe = True
            self.features.has_unsafe_deserialization = True
        
        elif 'system' in func_name:
            self.features.uses_os_system = True
            self.features.has_command_injection_risk = True
        
        elif func_name == 'subprocess.call' or func_name == 'subprocess.Popen':
            # Verificar si shell=True
            for keyword in node.keywords:
                if keyword.arg == 'shell' and isinstance(keyword.value, ast.Constant):
                    if keyword.value.value is True:
                        self.features.uses_subprocess_shell = True
                        self.features.has_command_injection_risk = True
    
    def _analyze_import(self, node):
        """Analiza imports para detectar módulos peligrosos o deprecados"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in self.DEPRECATED_MODULES:
                    self.features.uses_deprecated_libs = True
                elif alias.name == 'os':
                    # Marcar para análisis posterior
                    pass
        
        elif isinstance(node, ast.ImportFrom):
            if node.module in self.DEPRECATED_MODULES:
                self.features.uses_deprecated_libs = True
            
            # Detectar criptografía débil
            for alias in node.names:
                if any(weak in alias.name.upper() for weak in self.WEAK_CRYPTO):
                    self.features.uses_weak_crypto = True
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Obtiene el nombre completo de una llamada a función"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return ''
    
    def _has_validation(self, node: ast.Call) -> bool:
        """Verifica si hay validación después de input()"""
        # Simplificado: en un análisis real se verificaría el contexto
        return False
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcula complejidad ciclomática de una función"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _calculate_derived_metrics(self):
        """Calcula métricas derivadas"""
        if self.function_complexities:
            self.features.max_function_complexity = max(self.function_complexities)
            self.features.avg_function_complexity = sum(self.function_complexities) / len(self.function_complexities)
        
        if self.features.num_functions > 0:
            # Estimar ratio de manejo de excepciones
            self.features.exception_handling_ratio = 0.5 if not self.features.has_bare_except else 0.2


def analyze_directory(directory: str) -> List[Dict[str, Any]]:
    """Analiza todos los archivos Python en un directorio"""
    results = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                analyzer = CodeAnalyzer()
                result = analyzer.analyze_file(filepath)
                results.append(result)
    
    return results


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Uso: python code_analyzer.py <directorio>")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    results = analyze_directory(target_dir)
    
    print(json.dumps(results, indent=2))
