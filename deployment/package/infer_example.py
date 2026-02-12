#!/usr/bin/env python3
"""
Inferencia rápida usando el modelo pre-entrenado.

Uso:
  python deployment/infer_example.py <ruta_a_archivo.py> [ruta_modelo]

El script analiza el archivo indicado, extrae características y ejecuta
la predicción usando `ml_model/vulnerability_detector.pkl` por defecto.
"""
import sys
import os
import json

from ml_model.model import VulnerabilityPredictor
from scripts.code_analyzer import CodeAnalyzer


def load_predictor(model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
    return VulnerabilityPredictor(model_path)


def analyze_file(path: str):
    analyzer = CodeAnalyzer()
    res = analyzer.analyze_file(path)
    return res.get('features', {})


def main():
    if len(sys.argv) < 2:
        print("Uso: python deployment/infer_example.py <ruta_a_archivo.py> [ruta_modelo]")
        sys.exit(1)

    file_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else 'ml_model/vulnerability_detector.pkl'

    predictor = load_predictor(model_path)

    features = analyze_file(file_path)
    df = predictor.prepare_features(features)

    pred, prob = predictor.predict(df)

    output = {
        'file': file_path,
        'prediction': int(pred),
        'probability': float(prob),
        'is_trained': predictor.is_trained
    }

    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
