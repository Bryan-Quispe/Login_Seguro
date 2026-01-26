#!/usr/bin/env python3
"""
Login Seguro - Script de Análisis de Seguridad con Bandit
Ejecuta análisis estático del código Python para detectar vulnerabilidades.
"""
import subprocess
import sys
import json
import os
from datetime import datetime
from pathlib import Path


def run_bandit_analysis():
    """Ejecuta Bandit y genera reporte de seguridad."""
    
    print("=" * 60)
    print("🔒 LOGIN SEGURO - Análisis de Seguridad con Bandit")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Directorio del backend
    backend_dir = Path(__file__).parent
    app_dir = backend_dir / "app"
    
    if not app_dir.exists():
        print("❌ Error: Directorio 'app' no encontrado")
        sys.exit(1)
    
    # Verificar que Bandit está instalado
    try:
        subprocess.run(["bandit", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Bandit no está instalado")
        print("   Instalar con: pip install bandit")
        sys.exit(1)
    
    print(f"📁 Analizando: {app_dir}")
    print()
    
    # Ejecutar Bandit
    output_file = backend_dir / "security_report_bandit.json"
    
    cmd = [
        "bandit",
        "-r", str(app_dir),
        "-f", "json",
        "-o", str(output_file),
        "--exclude", "tests,__pycache__",
        "-ll"  # Solo reportar Medium y High severity
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        print(f"❌ Error ejecutando Bandit: {e}")
        sys.exit(1)
    
    # Parsear resultados
    if output_file.exists():
        with open(output_file, "r") as f:
            report = json.load(f)
        
        metrics = report.get("metrics", {})
        results = report.get("results", [])
        
        # Contar por severidad
        high_issues = sum(1 for r in results if r.get("issue_severity") == "HIGH")
        medium_issues = sum(1 for r in results if r.get("issue_severity") == "MEDIUM")
        low_issues = sum(1 for r in results if r.get("issue_severity") == "LOW")
        
        print("📊 RESULTADOS DEL ANÁLISIS")
        print("-" * 40)
        print(f"   🔴 Alta severidad:   {high_issues}")
        print(f"   🟠 Media severidad:  {medium_issues}")
        print(f"   🟡 Baja severidad:   {low_issues}")
        print(f"   📝 Total issues:     {len(results)}")
        print()
        
        # Mostrar detalles de issues críticos
        if high_issues > 0:
            print("⚠️  ISSUES DE ALTA SEVERIDAD:")
            print("-" * 40)
            for r in results:
                if r.get("issue_severity") == "HIGH":
                    print(f"   📍 {r.get('filename')}:{r.get('line_number')}")
                    print(f"      {r.get('issue_text')}")
                    print(f"      CWE: {r.get('issue_cwe', {}).get('id', 'N/A')}")
                    print()
        
        # Mostrar líneas analizadas
        total_loc = sum(m.get("loc", 0) for m in metrics.values() if isinstance(m, dict))
        print(f"📈 Líneas de código analizadas: {total_loc}")
        print(f"💾 Reporte guardado en: {output_file}")
        
        if high_issues > 0:
            print("\n🚨 ¡Se encontraron vulnerabilidades críticas!")
            return 1
        elif medium_issues > 0:
            print("\n⚠️  Se encontraron vulnerabilidades de nivel medio")
            return 0
        else:
            print("\n✅ No se detectaron vulnerabilidades críticas")
            return 0
    else:
        print("❌ Error: No se generó el reporte")
        return 1


if __name__ == "__main__":
    sys.exit(run_bandit_analysis())
