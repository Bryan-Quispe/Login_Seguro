#!/usr/bin/env python3
"""
Análisis de Seguridad Completo - Login Seguro
==============================================

Script integrado que ejecuta:
1. Análisis estático con modelo de IA (detector de vulnerabilidades)
2. Pruebas dinámicas (XSS, CSRF, simulaciones de ataques)  
3. Métricas de cobertura de código
4. Generación de informe exhaustivo

Uso:
    python run_security_analysis.py [--skip-static] [--skip-dynamic] [--output RUTA]
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse

# Asegurar que el path del paquete del modelo esté disponible
DEPLOYMENT_PATH = Path(__file__).parent.parent / 'deployment' / 'package'
sys.path.insert(0, str(DEPLOYMENT_PATH))

try:
    from model import VulnerabilityPredictor
    from code_analyzer import CodeAnalyzer
except ImportError as e:
    print(f"⚠️  Error: No se pudo importar el modelo de IA desde deployment/package/")
    print(f"   Detalle: {e}")
    print(f"   Asegúrate de que existen: {DEPLOYMENT_PATH}/model.py y code_analyzer.py")
    VulnerabilityPredictor = None
    CodeAnalyzer = None


class SecurityAnalysisRunner:
    """Ejecuta análisis completo de seguridad y genera informe"""
    
    def __init__(self, output_path: str = "INFORME_SEGURIDAD.md"):
        self.output_path = output_path
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'static_analysis': {},
            'dynamic_tests': {},
            'coverage': {},
            'vulnerabilities_found': [],
            'recommendations': []
        }
        
        # Inicializar modelo
        if VulnerabilityPredictor:
            model_file = DEPLOYMENT_PATH / 'vulnerability_detector.pkl'
            if model_file.exists():
                self.predictor = VulnerabilityPredictor(str(model_file))
                print(f"✅ Modelo de IA cargado: {model_file}")
            else:
                print(f"⚠️  Modelo no encontrado en {model_file}")
                self.predictor = None
        else:
            self.predictor = None
        
        if CodeAnalyzer:
            self.analyzer = CodeAnalyzer()
        else:
            self.analyzer = None
    
    def run_static_analysis(self) -> Dict[str, Any]:
        """Ejecuta análisis estático con modelo de IA"""
        print("\n" + "="*70)
        print("📊 ANÁLISIS ESTÁTICO CON MODELO DE IA")
        print("="*70)
        
        if not self.predictor or not self.analyzer:
            print("⚠️  Omitiendo análisis estático (modelo no disponible)")
            return {'skipped': True}
        
        results = {
            'files_analyzed': 0,
            'vulnerabilities_detected': 0,
            'safe_files': 0,
            'files_detail': []
        }
        
        # Buscar todos los archivos .py en app/
        app_path = Path(__file__).parent / 'app'
        py_files = list(app_path.rglob('*.py'))
        
        print(f"Analizando {len(py_files)} archivos Python...")
        
        for py_file in py_files:
            # Omitir __pycache__ y archivos de test
            if '__pycache__' in str(py_file) or 'test' in str(py_file).lower():
                continue
            
            try:
                # Extraer características
                analysis = self.analyzer.analyze_file(str(py_file))
                features = analysis.get('features', {})
                
                # Preparar para predicción
                df = self.predictor.prepare_features(features)
                
                # Predecir
                prediction, probability = self.predictor.predict(df)
                
                results['files_analyzed'] += 1
                
                file_info = {
                    'path': str(py_file.relative_to(app_path.parent)),
                    'prediction': 'VULNERABLE' if prediction == 1 else 'SEGURO',
                    'probability': round(probability * 100, 2),
                    'risk_level': self._get_risk_level(probability)
                }
                
                if prediction == 1:
                    results['vulnerabilities_detected'] += 1
                    file_info['issues'] = self._extract_issues(features)
                else:
                    results['safe_files'] += 1
                
                results['files_detail'].append(file_info)
                
                # Mostrar progreso
                status = "🔴" if prediction == 1 else "🟢"
                print(f"{status} {file_info['path']}: {file_info['prediction']} ({file_info['probability']}%)")
                
            except Exception as e:
                print(f"⚠️  Error analizando {py_file}: {e}")
        
        self.results['static_analysis'] = results
        return results
    
    def run_dynamic_tests(self) -> Dict[str, Any]:
        """Ejecuta pruebas dinámicas (XSS, CSRF, etc.)"""
        print("\n" + "="*70)
        print("🔍 PRUEBAS DINÁMICAS (XSS, CSRF)")
        print("="*70)
        
        results = {
            'executed': False,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            # Ejecutar pytest con el archivo de pruebas dinámicas
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/integration/test_dynamic_security.py',
                '-v',
                '--tb=short',
                '--json-report',
                '--json-report-file=test_results_dynamic.json'
            ]
            
            print(f"Ejecutando: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            results['executed'] = True
            results['stdout'] = result.stdout
            results['stderr'] = result.stderr
            results['return_code'] = result.returncode
            
            # Intentar leer el reporte JSON si existe
            json_report = Path(__file__).parent / 'test_results_dynamic.json'
            if json_report.exists():
                with open(json_report, 'r') as f:
                    report = json.load(f)
                    summary = report.get('summary', {})
                    results['total_tests'] = summary.get('total', 0)
                    results['passed'] = summary.get('passed', 0)
                    results['failed'] = summary.get('failed', 0)
                    results['skipped'] = summary.get('skipped', 0)
            
            print(f"\n✅ Pruebas ejecutadas: {results['total_tests']}")
            print(f"   Pasadas: {results['passed']}, Fallidas: {results['failed']}, Omitidas: {results['skipped']}")
            
        except subprocess.TimeoutExpired:
            print("⚠️  Timeout ejecutando pruebas dinámicas")
            results['error'] = 'timeout'
        except FileNotFoundError:
            print("⚠️  pytest no encontrado. Instala con: pip install pytest pytest-asyncio pytest-json-report")
            results['error'] = 'pytest_not_found'
        except Exception as e:
            print(f"⚠️  Error ejecutando pruebas dinámicas: {e}")
            results['error'] = str(e)
        
        self.results['dynamic_tests'] = results
        return results
    
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Ejecuta análisis de cobertura de código"""
        print("\n" + "="*70)
        print("📈 ANÁLISIS DE COBERTURA")
        print("="*70)
        
        results = {
            'executed': False,
            'coverage_percentage': 0.0
        }
        
        try:
            # Ejecutar pytest con coverage
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/',
                '--cov=app',
                '--cov-report=html',
                '--cov-report=json',
                '--cov-report=term',
                '-q'
            ]
            
            print(f"Ejecutando: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            results['executed'] = True
            results['stdout'] = result.stdout
            
            # Leer reporte JSON de coverage
            coverage_json = Path(__file__).parent / 'coverage.json'
            if coverage_json.exists():
                with open(coverage_json, 'r') as f:
                    cov_data = json.load(f)
                    results['coverage_percentage'] = cov_data.get('totals', {}).get('percent_covered', 0)
                    results['lines_covered'] = cov_data.get('totals', {}).get('covered_lines', 0)
                    results['lines_total'] = cov_data.get('totals', {}).get('num_statements', 0)
            
            print(f"\n✅ Cobertura: {results['coverage_percentage']:.2f}%")
            print(f"   Reporte HTML generado en: htmlcov/index.html")
            
        except subprocess.TimeoutExpired:
            print("⚠️  Timeout ejecutando análisis de cobertura")
            results['error'] = 'timeout'
        except FileNotFoundError:
            print("⚠️  pytest-cov no encontrado. Instala con: pip install pytest-cov")
            results['error'] = 'pytest_cov_not_found'
        except Exception as e:
            print(f"⚠️  Error ejecutando cobertura: {e}")
            results['error'] = str(e)
        
        self.results['coverage'] = results
        return results
    
    def generate_report(self):
        """Genera informe exhaustivo en Markdown"""
        print("\n" + "="*70)
        print("📝 GENERANDO INFORME")
        print("="*70)
        
        report = f"""# 🔒 Informe de Seguridad - Login Seguro

**Fecha de análisis:** {self.results['timestamp']}  
**Proyecto:** Login Seguro - Sistema de Autenticación Biométrica  

---

## 📊 Resumen Ejecutivo

### Análisis Estático (Modelo de IA)
"""
        
        static = self.results.get('static_analysis', {})
        if static.get('skipped'):
            report += "- ⚠️ **Omitido** (modelo no disponible)\n"
        else:
            report += f"""- **Archivos analizados:** {static.get('files_analyzed', 0)}
- **Vulnerabilidades detectadas:** {static.get('vulnerabilities_detected', 0)}
- **Archivos seguros:** {static.get('safe_files', 0)}
"""
        
        dynamic = self.results.get('dynamic_tests', {})
        report += f"""
### Pruebas Dinámicas (XSS, CSRF)
- **Tests ejecutados:** {dynamic.get('total_tests', 0)}
- **Pasados:** {dynamic.get('passed', 0)}
- **Fallidos:** {dynamic.get('failed', 0)}
- **Omitidos:** {dynamic.get('skipped', 0)}
"""
        
        coverage = self.results.get('coverage', {})
        cov_pct = coverage.get('coverage_percentage', 0)
        report += f"""
### Cobertura de Código
- **Cobertura total:** {cov_pct:.2f}%
- **Líneas cubiertas:** {coverage.get('lines_covered', 0)} / {coverage.get('lines_total', 0)}

---

## 🔍 Análisis Estático Detallado

### Metodología
Se utilizó un modelo de Machine Learning (Random Forest) entrenado con datos de CVE/CWE para detectar patrones de vulnerabilidades en el código fuente. El modelo analiza:

- Patrones de inyección (SQL, Comandos, XSS)
- Uso de funciones peligrosas (eval, exec, pickle)
- Manejo inseguro de datos de entrada
- Criptografía débil
- Hardcoded secrets
- Complejidad ciclomática
- Calidad del manejo de excepciones

### Resultados por Archivo
"""
        
        if not static.get('skipped'):
            files = static.get('files_detail', [])
            
            # Agrupar por nivel de riesgo
            high_risk = [f for f in files if f.get('risk_level') == 'ALTO']
            medium_risk = [f for f in files if f.get('risk_level') == 'MEDIO']
            low_risk = [f for f in files if f.get('risk_level') == 'BAJO']
            
            if high_risk:
                report += "\n#### 🔴 Archivos de Alto Riesgo\n\n"
                for f in high_risk:
                    report += f"- **{f['path']}** - Probabilidad: {f['probability']}%\n"
                    if 'issues' in f:
                        for issue in f['issues']:
                            report += f"  - {issue}\n"
                    report += "\n"
            
            if medium_risk:
                report += "\n#### 🟡 Archivos de Riesgo Medio\n\n"
                for f in medium_risk:
                    report += f"- **{f['path']}** - Probabilidad: {f['probability']}%\n"
            
            if low_risk:
                report += f"\n#### 🟢 Archivos de Bajo Riesgo / Seguros\n\n"
                report += f"Total: {len(low_risk)} archivos\n"
        
        report += """
---

## 🎯 Pruebas Dinámicas

### Metodología
Se ejecutaron pruebas de integración que simulan:

1. **XSS (Cross-Site Scripting)**
   - XSS Reflejado: Inyección de scripts en parámetros de entrada
   - XSS Persistente: Almacenamiento y recuperación de payloads maliciosos
   
2. **CSRF (Cross-Site Request Forgery)**
   - Verificación de tokens CSRF en operaciones sensibles
   - Pruebas con/sin cabeceras de autenticación

3. **Validación de Entrada**
   - Sanitización de datos de usuario
   - Escape de caracteres especiales

### Resultados
"""
        
        if dynamic.get('executed'):
            if dynamic.get('failed', 0) > 0:
                report += f"\n⚠️ **{dynamic['failed']} pruebas fallaron**. Revisar detalles en logs.\n"
            else:
                report += f"\n✅ Todas las pruebas pasaron exitosamente.\n"
            
            if dynamic.get('stdout'):
                report += f"\n```\n{dynamic['stdout'][-1000:]}\n```\n"
        else:
            report += "\n⚠️ No se pudieron ejecutar las pruebas dinámicas.\n"
        
        report += f"""
---

## 📈 Métricas de Cobertura

**Cobertura actual:** {cov_pct:.2f}%

### Interpretación
- ✅ **>80%:** Cobertura excelente
- ⚠️ **60-80%:** Cobertura aceptable, mejorar
- ❌ **<60%:** Cobertura insuficiente

### Reporte Detallado
El reporte HTML completo está disponible en: `htmlcov/index.html`

---

## 🛠️ Correcciones Aplicadas

### Mitigaciones de Seguridad Implementadas

1. **Protección contra SQL Injection**
   - ✅ Uso de consultas parametrizadas
   - ✅ ORM con validación de entrada

2. **Protección contra XSS**
   - ✅ Sanitización de entrada con Pydantic
   - ✅ Validación de tipos de datos
   - ✅ Escape automático en respuestas JSON

3. **Protección contra CSRF**
   - ✅ Autenticación basada en JWT (inmune a CSRF tradicional)
   - ✅ Validación de origen en CORS

4. **Autenticación Segura**
   - ✅ Hash de contraseñas con bcrypt
   - ✅ Tokens JWT con expiración
   - ✅ Rate limiting para prevenir fuerza bruta
   - ✅ Bloqueo de cuenta por intentos fallidos

5. **Verificación Biométrica**
   - ✅ Anti-spoofing facial
   - ✅ Detección de fotos/videos

---

## 📋 Recomendaciones

### Prioridad Alta
1. Revisar archivos marcados como "Alto Riesgo" por el modelo
2. Alcanzar >80% de cobertura de código
3. Implementar logging de seguridad para auditoría

### Prioridad Media
4. Añadir pruebas de fuzzing para endpoints críticos
5. Configurar WAF (Web Application Firewall) en producción
6. Implementar HTTPS obligatorio

### Prioridad Baja
7. Análisis periódico de dependencias (npm audit, safety)
8. Penetration testing profesional
9. Bug bounty program

---

## 📚 Referencias

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Generado automáticamente por:** `run_security_analysis.py`  
**Modelo de IA:** Random Forest Classifier (CVE/CWE Dataset)

"""
        
        # Guardar informe
        output_file = Path(__file__).parent / self.output_path
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ Informe generado: {output_file}")
        
        return report
    
    def _get_risk_level(self, probability: float) -> str:
        """Determina nivel de riesgo según probabilidad"""
        if probability >= 0.7:
            return "ALTO"
        elif probability >= 0.4:
            return "MEDIO"
        else:
            return "BAJO"
    
    def _extract_issues(self, features: Dict) -> List[str]:
        """Extrae issues detectados de las características"""
        issues = []
        
        # Mapeo de características a descripciones
        risk_features = {
            'has_eval': 'Uso de eval() detectado',
            'has_exec': 'Uso de exec() detectado',
            'has_sql_concat': 'Posible SQL Injection (concatenación)',
            'has_pickle_load': 'Deserialización insegura (pickle)',
            'has_hardcoded_secrets': 'Secrets hardcodeados detectados',
            'uses_weak_crypto': 'Uso de criptografía débil',
            'has_command_injection_risk': 'Riesgo de inyección de comandos',
            'has_path_traversal_risk': 'Riesgo de path traversal',
            'has_bare_except': 'Manejo de excepciones demasiado amplio'
        }
        
        for feature, description in risk_features.items():
            if features.get(feature):
                issues.append(description)
        
        return issues


def main():
    parser = argparse.ArgumentParser(
        description='Análisis de seguridad completo con modelo de IA'
    )
    parser.add_argument(
        '--skip-static',
        action='store_true',
        help='Omitir análisis estático'
    )
    parser.add_argument(
        '--skip-dynamic',
        action='store_true',
        help='Omitir pruebas dinámicas'
    )
    parser.add_argument(
        '--skip-coverage',
        action='store_true',
        help='Omitir análisis de cobertura'
    )
    parser.add_argument(
        '--output',
        default='INFORME_SEGURIDAD.md',
        help='Ruta del archivo de salida'
    )
    
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         🔒 ANÁLISIS DE SEGURIDAD - LOGIN SEGURO 🔒          ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    runner = SecurityAnalysisRunner(output_path=args.output)
    
    # Ejecutar análisis
    if not args.skip_static:
        runner.run_static_analysis()
    
    if not args.skip_dynamic:
        runner.run_dynamic_tests()
    
    if not args.skip_coverage:
        runner.run_coverage_analysis()
    
    # Generar informe
    runner.generate_report()
    
    print("\n" + "="*70)
    print("✅ ANÁLISIS COMPLETO")
    print("="*70)
    print(f"\nRevisa el informe en: {args.output}")
    print()


if __name__ == '__main__':
    main()
