# Deployment package: usar modelo entrenado

Archivos mínimos que debes copiar al otro proyecto para usar el modelo ya entrenado:

- `ml_model/vulnerability_detector.pkl`  # archivo del modelo (pickle)
- `ml_model/model.py`                    # clase `VulnerabilityPredictor`
- `scripts/code_analyzer.py`             # extractor de features desde archivos .py
- `deployment/infer_example.py`          # script de inferencia (este archivo)
- `requirements.txt`                     # dependencias del entorno (instalar antes)
- `config.yml` (opcional)                # si tu integración usa rutas/valores de config

Pasos rápidos para probar en la máquina destino:

1. Copia los archivos listados manteniendo la estructura de carpetas.

2. Instala dependencias (recomendado crear virtualenv):

```bash
python -m venv .venv
source .venv/bin/activate   # o .venv\Scripts\activate en Windows
python -m pip install -r requirements.txt
```

3. Ejecuta una inferencia sobre un archivo Python de ejemplo:

```bash
python deployment/infer_example.py ruta/al/archivo.py ml_model/vulnerability_detector.pkl
```

Salida: JSON con `prediction` (0=seguro, 1=vulnerable) y `probability`.

Notas:
- Si tu pipeline usa un extractor diferente, copia también el script correspondiente.
- Si el `.pkl` es grande, distribúyelo vía release del repositorio o un almacenamiento compartido y descarga en `ml_model/`.
