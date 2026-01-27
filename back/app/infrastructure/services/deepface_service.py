"""
Login Seguro - Servicio de Reconocimiento Facial con OpenCV
Implementa IFaceService con detección básica de rostro
Compatible con Python 3.14
"""
import base64
import io
import json
import logging
import hashlib
from typing import Tuple, Optional, List

import numpy as np
import cv2

from ...domain.interfaces.face_service import IFaceService
from ...config.settings import get_settings

logger = logging.getLogger(__name__)


class OpenCVFaceService(IFaceService):
    """
    Implementación del servicio de reconocimiento facial usando OpenCV.
    Compatible con todas las versiones de Python.
    """
    
    def __init__(self):
        self._settings = get_settings()
        self._threshold = self._settings.FACE_DISTANCE_THRESHOLD
        
        # Cargar clasificador Haar para detección de rostros
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        logger.info("OpenCV Face Service inicializado")
    
    def _decode_image(self, image_data: bytes) -> np.ndarray:
        """Decodifica una imagen desde base64."""
        try:
            if isinstance(image_data, str):
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("No se pudo decodificar la imagen")
            
            return img
            
        except Exception as e:
            logger.error(f"Error decodificando imagen: {e}")
            raise ValueError(f"Imagen inválida: {str(e)}")
    
    def _detect_face(self, img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Detecta el rostro más grande en la imagen."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Parámetros más permisivos para detección
        faces = self._face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.05,  # Más fino para mejor detección
            minNeighbors=3,    # Menos estricto
            minSize=(80, 80),  # Tamaño mínimo más pequeño
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) == 0:
            # Intentar con parámetros aún más permisivos
            faces = self._face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=2, minSize=(60, 60)
            )
            if len(faces) == 0:
                return None
        
        # Retornar el rostro más grande
        largest = max(faces, key=lambda f: f[2] * f[3])
        return tuple(largest)
    
    def _compute_lbp(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Calcula Local Binary Pattern (LBP) de la imagen.
        LBP es robusto a cambios de iluminación.
        """
        rows, cols = gray_image.shape
        lbp = np.zeros((rows-2, cols-2), dtype=np.uint8)
        
        for i in range(1, rows-1):
            for j in range(1, cols-1):
                center = gray_image[i, j]
                code = 0
                # 8 vecinos en sentido horario
                code |= (gray_image[i-1, j-1] >= center) << 7
                code |= (gray_image[i-1, j] >= center) << 6
                code |= (gray_image[i-1, j+1] >= center) << 5
                code |= (gray_image[i, j+1] >= center) << 4
                code |= (gray_image[i+1, j+1] >= center) << 3
                code |= (gray_image[i+1, j] >= center) << 2
                code |= (gray_image[i+1, j-1] >= center) << 1
                code |= (gray_image[i, j-1] >= center) << 0
                lbp[i-1, j-1] = code
        
        return lbp
    
    def _extract_face_features(self, img: np.ndarray, face_rect: Tuple[int, int, int, int]) -> List[float]:
        """
        Extrae características del rostro usando LBP (Local Binary Patterns).
        LBP es robusto a cambios de iluminación y fondo.
        Solo analiza la CARA, no el fondo.
        """
        x, y, w, h = face_rect
        
        # Agregar pequeño margen y recortar solo la cara
        margin_x = int(w * 0.05)
        margin_y = int(h * 0.05)
        x1 = max(0, x + margin_x)
        y1 = max(0, y + margin_y)
        x2 = min(img.shape[1], x + w - margin_x)
        y2 = min(img.shape[0], y + h - margin_y)
        
        face_roi = img[y1:y2, x1:x2]
        
        # Redimensionar a tamaño fijo (solo la cara)
        face_resized = cv2.resize(face_roi, (128, 128))
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        
        # Ecualizar histograma para normalizar iluminación
        gray = cv2.equalizeHist(gray)
        
        # Calcular LBP (robusto a iluminación)
        lbp = self._compute_lbp(gray)
        
        # Dividir la cara en regiones y calcular histograma LBP por región
        # Esto captura la estructura espacial del rostro
        features = []
        grid_x, grid_y = 8, 8  # 8x8 = 64 regiones
        cell_h, cell_w = lbp.shape[0] // grid_y, lbp.shape[1] // grid_x
        
        for i in range(grid_y):
            for j in range(grid_x):
                cell = lbp[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                hist, _ = np.histogram(cell, bins=16, range=(0, 256))
                hist = hist.astype(np.float32)
                hist /= (hist.sum() + 1e-7)  # Normalizar
                features.extend(hist.tolist())
        
        return features
    
    def extract_face_encoding(self, image_data: bytes) -> Tuple[bool, Optional[List[float]], str]:
        """Extrae el encoding facial de una imagen."""
        try:
            img = self._decode_image(image_data)
            
            # Detectar rostro
            face_rect = self._detect_face(img)
            if face_rect is None:
                return False, None, "No se detectó ningún rostro en la imagen"
            
            # Verificar anti-spoofing básico
            is_real, confidence, spoof_msg = self.detect_spoofing(image_data)
            if not is_real:
                return False, None, f"Spoofing detectado: {spoof_msg}"
            
            # Extraer características
            encoding = self._extract_face_features(img, face_rect)
            
            logger.info("Encoding facial extraído exitosamente")
            return True, encoding, "Encoding facial extraído correctamente"
            
        except Exception as e:
            logger.error(f"Error extrayendo encoding facial: {e}")
            return False, None, f"Error al procesar imagen: {str(e)}"
    
    def verify_face(self, 
                   image_data: bytes, 
                   stored_encoding: List[float],
                   threshold: float = None) -> Tuple[bool, float, str]:
        """
        Verifica si el rostro coincide con el encoding almacenado.
        IMPORTANTE: Solo da acceso si el rostro coincide con el registrado.
        """
        # Threshold para verificación de identidad
        # Un threshold de 0.55 significa que la similitud debe ser > 45%
        # Valores más altos = más permisivo
        threshold = threshold or 0.55
        
        try:
            img = self._decode_image(image_data)
            
            # Detectar rostro
            face_rect = self._detect_face(img)
            if face_rect is None:
                return False, 1.0, "No se detectó rostro en la imagen"
            
            # Extraer características del rostro actual
            current_encoding = self._extract_face_features(img, face_rect)
            
            # Validar que los encodings tengan la misma longitud
            if len(current_encoding) != len(stored_encoding):
                logger.warning(f"Longitud de encodings no coincide: {len(current_encoding)} vs {len(stored_encoding)}")
                # Si no coinciden, podría ser un encoding antiguo, hacer comparación básica
                return False, 1.0, "Debe registrar su rostro nuevamente (formato de encoding actualizado)"
            
            # Convertir a numpy arrays
            current_np = np.array(current_encoding, dtype=np.float32)
            stored_np = np.array(stored_encoding, dtype=np.float32)
            
            # Método 1: Correlación de histogramas Chi-Square (mejor para LBP)
            chi_square = cv2.compareHist(current_np, stored_np, cv2.HISTCMP_CHISQR)
            # Chi-square: 0 = idénticos, mayor = más diferentes
            # Normalizar a [0, 1]
            chi_normalized = min(chi_square / 10.0, 1.0)
            
            # Método 2: Intersección de histogramas
            intersection = cv2.compareHist(current_np, stored_np, cv2.HISTCMP_INTERSECT)
            # Normalizar por el máximo posible
            max_intersection = min(np.sum(current_np), np.sum(stored_np))
            intersection_score = intersection / (max_intersection + 1e-7)
            
            # Método 3: Correlación (como backup)
            correlation = cv2.compareHist(current_np, stored_np, cv2.HISTCMP_CORREL)
            
            # Combinar scores: mayor = más similar
            # intersection_score: 0-1 (1 = igual)
            # correlation: -1 a 1 (1 = igual)
            # chi_normalized: 0-1 (0 = igual, invertir)
            
            combined_similarity = (
                intersection_score * 0.4 +     # 40% peso intersección
                (1 - chi_normalized) * 0.3 +   # 30% peso chi-square invertido
                max(0, correlation) * 0.3      # 30% peso correlación
            )
            
            # Distancia = 1 - similitud
            distance = 1.0 - combined_similarity
            
            # Threshold del .env (default 0.25 significa que similitud debe ser > 75%)
            is_match = distance < threshold
            
            logger.info(f"Comparación LBP - Intersección: {intersection_score:.4f}, Chi²: {chi_normalized:.4f}, Correlación: {correlation:.4f}")
            logger.info(f"Similitud combinada: {combined_similarity:.4f}, Distancia: {distance:.4f}, Threshold: {threshold}")
            
            if is_match:
                logger.info(f"✓ Verificación facial EXITOSA - Similitud: {combined_similarity*100:.1f}%")
                return True, distance, f"Verificación facial exitosa (similitud: {combined_similarity*100:.1f}%)"
            else:
                logger.warning(f"✗ Verificación facial FALLIDA - Similitud: {combined_similarity*100:.1f}%")
                return False, distance, f"El rostro no coincide con el registrado (similitud: {combined_similarity*100:.1f}%)"
            
        except Exception as e:
            logger.error(f"Error en verificación facial: {e}")
            return False, 1.0, f"Error al verificar rostro: {str(e)}"
    
    def detect_spoofing(self, image_data: bytes) -> Tuple[bool, float, str]:
        """
        Detecta si la imagen es un intento de spoofing usando análisis de textura.
        Técnica: análisis de varianza de Laplaciano (imágenes planas = fotos de fotos)
        """
        try:
            img = self._decode_image(image_data)
            
            # Detectar rostro primero
            face_rect = self._detect_face(img)
            if face_rect is None:
                return False, 0.0, "No se detectó ningún rostro"
            
            x, y, w, h = face_rect
            face_roi = img[y:y+h, x:x+w]
            
            # Análisis de textura con Laplaciano
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Umbral: fotos de fotos tienen menos variación
            # Valores típicos: pantalla/foto < 50, rostro real > 100
            texture_score = min(laplacian_var / 200.0, 1.0)
            
            # También verificar contraste
            contrast = gray.std()
            contrast_score = min(contrast / 50.0, 1.0)
            
            # Score combinado
            confidence = (texture_score * 0.7) + (contrast_score * 0.3)
            
            # Umbral de decisión (más permisivo para evitar falsos positivos)
            is_real = laplacian_var > 30 and contrast > 20
            
            if is_real:
                logger.info(f"Rostro real detectado (laplacian: {laplacian_var:.2f})")
                return True, confidence, "Rostro real verificado"
            else:
                logger.warning(f"Posible spoofing (laplacian: {laplacian_var:.2f})")
                return False, confidence, "Se detectó un posible intento de spoofing"
            
        except Exception as e:
            logger.error(f"Error en detección de spoofing: {e}")
            # En caso de error, permitir (evitar bloqueo)
            return True, 0.5, "No se pudo verificar anti-spoofing"
    
    def verify_face_with_antispoofing(self,
                                      image_data: bytes,
                                      stored_encoding: List[float],
                                      threshold: float = None) -> Tuple[bool, dict, str]:
        """Verificación completa: anti-spoofing + reconocimiento facial."""
        threshold = threshold or self._threshold
        
        # Paso 1: Verificar anti-spoofing
        is_real, spoof_confidence, spoof_msg = self.detect_spoofing(image_data)
        
        if not is_real:
            return False, {
                'is_real': False,
                'spoof_confidence': spoof_confidence,
                'face_match': False,
                'distance': 1.0
            }, f"Acceso denegado: {spoof_msg}"
        
        # Paso 2: Verificar coincidencia facial
        face_match, distance, face_msg = self.verify_face(
            image_data, stored_encoding, threshold
        )
        
        details = {
            'is_real': True,
            'spoof_confidence': spoof_confidence,
            'face_match': face_match,
            'distance': distance
        }
        
        if face_match:
            logger.info("Verificación biométrica completa exitosa")
            return True, details, "Verificación biométrica exitosa"
        else:
            logger.warning("Rostro real pero no coincide")
            return False, details, face_msg


# Alias para compatibilidad
DeepFaceService = OpenCVFaceService
MediaPipeFaceService = OpenCVFaceService
