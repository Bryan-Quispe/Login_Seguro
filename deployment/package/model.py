"""
Modelo predictivo de vulnerabilidades usando Random Forest.
Entrenado con datos reales de CVE/CWE del Dataset.
"""

import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from typing import Dict, List, Tuple
import os


class VulnerabilityPredictor:
    """Predictor de vulnerabilidades basado en Random Forest"""
    
    def __init__(self, model_path: str = None):
        """
        Inicializa el predictor
        
        Args:
            model_path: Ruta al modelo pre-entrenado. Si es None, crea uno nuevo.
        """
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced',
                n_jobs=-1
            )
            self.feature_names = []
            self.is_trained = False
    
    def prepare_features(self, features_dict: Dict) -> pd.DataFrame:
        """
        Prepara las características para el modelo
        
        Args:
            features_dict: Diccionario con características extraídas del código
            
        Returns:
            DataFrame con características preparadas
        """
        # Convertir booleanos a enteros
        features = features_dict.copy()
        for key, value in features.items():
            if isinstance(value, bool):
                features[key] = int(value)
        
        df = pd.DataFrame([features])
        
        # Si el modelo está entrenado, asegurar que las columnas coincidan
        if self.is_trained and self.feature_names:
            # Agregar columnas faltantes con valor 0
            for col in self.feature_names:
                if col not in df.columns:
                    df[col] = 0
            # Mantener solo las columnas del modelo
            df = df[self.feature_names]
        
        return df
    
    def train(self, X: pd.DataFrame, y: np.ndarray) -> Dict:
        """
        Entrena el modelo
        
        Args:
            X: DataFrame con características
            y: Array con etiquetas (0: seguro, 1: vulnerable)
            
        Returns:
            Diccionario con métricas de entrenamiento
        """
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Guardar nombres de características
        self.feature_names = list(X.columns)
        
        # Entrenar modelo
        print("Entrenando modelo Random Forest...")
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluar
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calcular métricas
        metrics = {
            'accuracy': self.model.score(X_test, y_test),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'feature_importance': dict(zip(
                self.feature_names,
                self.model.feature_importances_.tolist()
            ))
        }
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='roc_auc')
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        
        print(f"\nAccuracy: {metrics['accuracy']:.4f}")
        print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"Cross-validation: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")
        
        return metrics
    
    def predict(self, features: pd.DataFrame) -> Tuple[int, float]:
        """
        Predice si el código tiene vulnerabilidades
        
        Args:
            features: DataFrame con características del código
            
        Returns:
            Tupla (predicción, probabilidad) donde:
            - predicción: 0 (seguro) o 1 (vulnerable)
            - probabilidad: probabilidad de vulnerabilidad (0-1)
        """
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        prediction = self.model.predict(features)[0]
        probability = self.model.predict_proba(features)[0][1]
        
        return int(prediction), float(probability)
    
    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Obtiene las características más importantes
        
        Args:
            top_n: Número de características principales a retornar
            
        Returns:
            Lista de tuplas (nombre_característica, importancia)
        """
        if not self.is_trained:
            return []
        
        importance = list(zip(self.feature_names, self.model.feature_importances_))
        importance.sort(key=lambda x: x[1], reverse=True)
        
        return importance[:top_n]
    
    def save_model(self, filepath: str):
        """Guarda el modelo entrenado"""
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Modelo guardado en: {filepath}")
    
    def load_model(self, filepath: str):
        """Carga un modelo pre-entrenado"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        
        print(f"Modelo cargado desde: {filepath}")
