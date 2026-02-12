"""
Login Seguro - Servicio de Reconocimiento Facial con OpenCV DNN
Usa modelos pre-entrenados de deep learning para identificación biométrica real
- YuNet: Detección facial de alta precisión
- SFace: Embeddings de 128 dimensiones para reconocimiento
"""
import base64
import logging
import os
from typing import Tuple, Optional, List
from pathlib import Path

import numpy as np
import cv2

from ...domain.interfaces.face_service import IFaceService
from ...config.settings import get_settings

logger = logging.getLogger(__name__)

# Directorio de modelos
MODELS_DIR = Path(__file__).parent.parent.parent.parent / "models"


class OpenCVDNNFaceService(IFaceService):
    """
    Servicio de reconocimiento facial usando modelos de deep learning.
    - YuNet: Detector facial de alta precisión
    - SFace: Red neuronal para embeddings faciales de 128 dimensiones
    """
    
    def __init__(self):
        self._settings = get_settings()
        self._threshold = self._settings.FACE_DISTANCE_THRESHOLD
        
        # Rutas de modelos
        yunet_path = MODELS_DIR / "face_detection_yunet.onnx"
        sface_path = MODELS_DIR / "face_recognition_sface.onnx"
        
        # Verificar modelos
        self._use_dnn = yunet_path.exists() and sface_path.exists()
        
        if self._use_dnn:
            try:
                # Inicializar detector YuNet
                self._detector = cv2.FaceDetectorYN.create(
                    str(yunet_path),
                    "",
                    (320, 320),
                    0.9,  # Score threshold
                    0.3,  # NMS threshold
                    5000  # Top K
                )
                
                # Inicializar reconocedor SFace
                self._recognizer = cv2.FaceRecognizerSF.create(
                    str(sface_path),
                    ""
                )
                
                logger.info(" Servicio DNN inicializado con YuNet + SFace")
            except Exception as e:
                logger.error(f"Error inicializando DNN: {e}")
                self._use_dnn = False
        else:
            logger.warning(" Modelos DNN no encontrados, usando Haar Cascade")
        
        # Fallback: clasificadores Haar
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def _decode_image(self, image_data: bytes) -> np.ndarray:
        """Decodifica imagen desde base64."""
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
    
    def _detect_face_dnn(self, img: np.ndarray) -> Optional[np.ndarray]:
        """Detecta rostro usando YuNet (DNN)."""
        h, w = img.shape[:2]
        self._detector.setInputSize((w, h))
        
        _, faces = self._detector.detect(img)
        
        if faces is None or len(faces) == 0:
            return None
        
        # Retornar el rostro con mayor score
        return faces[0]
    
    def _detect_face_haar(self, img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Detecta rostro usando Haar Cascade (fallback)."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = self._face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )
        
        if len(faces) == 0:
            return None
        
        largest = max(faces, key=lambda f: f[2] * f[3])
        return tuple(largest)
    
    def _extract_embedding_dnn(self, img: np.ndarray, face: np.ndarray) -> np.ndarray:
        """Extrae embedding de 128 dimensiones usando SFace."""
        # Alinear rostro
        aligned = self._recognizer.alignCrop(img, face)
        
        # Extraer embedding (128 dimensiones)
        embedding = self._recognizer.feature(aligned)
        
        return embedding.flatten()
    
    def _extract_embedding_fallback(self, img: np.ndarray, face_rect: Tuple[int, int, int, int]) -> List[float]:
        """Extrae características usando LBP (fallback si no hay DNN)."""
        x, y, w, h = face_rect
        face_roi = img[y:y+h, x:x+w]
        
        # Redimensionar
        face_resized = cv2.resize(face_roi, (128, 128))
        gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        
        # CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # LBP simplificado
        features = []
        rows, cols = gray.shape
        
        for i in range(1, rows-1, 4):
            for j in range(1, cols-1, 4):
                center = gray[i, j]
                code = 0
                code |= (gray[i-1, j] >= center) << 0
                code |= (gray[i, j+1] >= center) << 1
                code |= (gray[i+1, j] >= center) << 2
                code |= (gray[i, j-1] >= center) << 3
                features.append(code / 15.0)
        
        return features
    
    def extract_face_encoding(self, image_data: bytes) -> Tuple[bool, Optional[List[float]], str]:
        """Extrae el encoding facial de una imagen."""
        try:
            img = self._decode_image(image_data)
            
            # Anti-spoofing
            is_real, _, spoof_msg = self.detect_spoofing(image_data)
            if not is_real:
                return False, None, f"Spoofing detectado: {spoof_msg}"
            
            if self._use_dnn:
                # Usar modelos DNN
                face = self._detect_face_dnn(img)
                if face is None:
                    return False, None, "No se detectó ningún rostro"
                
                embedding = self._extract_embedding_dnn(img, face)
                encoding = embedding.tolist()
                
                logger.info(f"✅ Encoding DNN extraído: {len(encoding)} dimensiones")
            else:
                # Fallback a Haar + LBP
                face_rect = self._detect_face_haar(img)
                if face_rect is None:
                    return False, None, "No se detectó ningún rostro"
                
                encoding = self._extract_embedding_fallback(img, face_rect)
                logger.info(f"⚠️ Encoding fallback extraído: {len(encoding)} características")
            
            return True, encoding, "Encoding facial extraído correctamente"
            
        except Exception as e:
            logger.error(f"Error extrayendo encoding: {e}")
            return False, None, f"Error: {str(e)}"
    
    def verify_face(self, 
                   image_data: bytes, 
                   stored_encoding: List[float],
                   threshold: float = None) -> Tuple[bool, float, str]:
        """
        Verifica si el rostro coincide con el encoding almacenado.
        Usa matching de SFace si está disponible.
        """
        # Threshold para SFace: 0.363 por defecto (cosine)
        # Más estricto: 0.30 significa 70% similitud
        threshold = threshold or 0.30
        
        try:
            img = self._decode_image(image_data)
            
            if self._use_dnn:
                # Detectar rostro con YuNet
                face = self._detect_face_dnn(img)
                if face is None:
                    return False, 1.0, "No se detectó rostro"
                
                # Extraer embedding actual
                current_embedding = self._extract_embedding_dnn(img, face)
                stored_embedding = np.array(stored_encoding, dtype=np.float32)
                
                # Verificar compatibilidad
                if len(current_embedding) != len(stored_embedding):
                    return False, 1.0, "Registre su rostro nuevamente"
                
                # Calcular similitud coseno usando SFace
                # Reshape para FaceRecognizerSF
                current_embed_2d = current_embedding.reshape(1, -1)
                stored_embed_2d = stored_embedding.reshape(1, -1)
                
                # Similitud coseno (1.0 = idéntico, 0.0 = diferente)
                cosine_score = self._recognizer.match(
                    current_embed_2d, stored_embed_2d, 
                    cv2.FaceRecognizerSF_FR_COSINE
                )
                
                # Distancia L2 normalizada
                l2_score = self._recognizer.match(
                    current_embed_2d, stored_embed_2d,
                    cv2.FaceRecognizerSF_FR_NORM_L2
                )
                
                # Combinar scores
                # cosine_score: 0-1 (1 = mejor)
                # l2_score: 0-2 (0 = mejor, normalizar)
                l2_similarity = max(0, 1 - l2_score / 2)
                
                combined = (cosine_score * 0.7 + l2_similarity * 0.3)
                distance = 1 - combined
                
                logger.info(f"=== VERIFICACIÓN DNN ===")
                logger.info(f"Coseno: {cosine_score:.4f}, L2: {l2_score:.4f}")
                logger.info(f"Similitud combinada: {combined*100:.1f}%")
                
                # Umbral estricto de similitud
                MIN_COSINE = 0.35  # Umbral recomendado por SFace
                
                if cosine_score < MIN_COSINE:
                    logger.warning(f"❌ RECHAZADO - Coseno: {cosine_score:.3f} < {MIN_COSINE}")
                    return False, float(distance), f"Rostro no coincide ({combined*100:.0f}%)"
                
                if distance >= threshold:
                    logger.warning(f"❌ RECHAZADO - Distancia: {distance:.3f}")
                    return False, float(distance), f"Rostro no coincide ({combined*100:.0f}%)"
                
                logger.info(f"✅ VERIFICACIÓN EXITOSA - {combined*100:.1f}%")
                return True, float(distance), f"Verificación exitosa ({combined*100:.0f}%)"
                
            else:
                # Fallback a LBP
                face_rect = self._detect_face_haar(img)
                if face_rect is None:
                    return False, 1.0, "No se detectó rostro"
                
                current = np.array(self._extract_embedding_fallback(img, face_rect))
                stored = np.array(stored_encoding)
                
                if len(current) != len(stored):
                    return False, 1.0, "Registre su rostro nuevamente"
                
                # Similitud coseno
                norm_c = np.linalg.norm(current)
                norm_s = np.linalg.norm(stored)
                
                if norm_c > 0 and norm_s > 0:
                    cosine = np.dot(current, stored) / (norm_c * norm_s)
                else:
                    cosine = 0.0
                
                distance = 1 - cosine
                
                if cosine < 0.90:  # 90% mínimo para LBP
                    return False, float(distance), f"Rostro no coincide ({cosine*100:.0f}%)"
                
                return True, float(distance), f"Verificación exitosa ({cosine*100:.0f}%)"
            
        except Exception as e:
            logger.error(f"Error en verificación: {e}")
            return False, 1.0, f"Error: {str(e)}"
    
    def detect_spoofing(self, image_data: bytes) -> Tuple[bool, float, str]:
        """Detecta intentos de spoofing con análisis de textura."""
        try:
            img = self._decode_image(image_data)
            
            if self._use_dnn:
                face = self._detect_face_dnn(img)
                if face is None:
                    return False, 0.0, "No se detectó rostro"
                
                x, y, w, h = int(face[0]), int(face[1]), int(face[2]), int(face[3])
            else:
                face_rect = self._detect_face_haar(img)
                if face_rect is None:
                    return False, 0.0, "No se detectó rostro"
                x, y, w, h = face_rect
            
            # Recortar región facial
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(img.shape[1], x + w)
            y2 = min(img.shape[0], y + h)
            
            face_roi = img[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                return False, 0.0, "Región facial inválida"
            
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # ===== Heurísticas Anti-Spoofing =====
            # 1) Textura (Laplacian) y contraste
            texture = min(laplacian_var / 220.0, 1.0)
            contrast = gray.std()
            contrast_score = min(contrast / 50.0, 1.0)

            # 2) Entropía de textura (LBP) para detectar pantallas/fotos lisas
            # LBP básico 3x3
            center = gray[1:-1, 1:-1]
            lbp = (
                ((gray[:-2, :-2] > center) << 7) |
                ((gray[:-2, 1:-1] > center) << 6) |
                ((gray[:-2, 2:] > center) << 5) |
                ((gray[1:-1, 2:] > center) << 4) |
                ((gray[2:, 2:] > center) << 3) |
                ((gray[2:, 1:-1] > center) << 2) |
                ((gray[2:, :-2] > center) << 1) |
                ((gray[1:-1, :-2] > center) << 0)
            ).astype(np.uint8)

            hist = cv2.calcHist([lbp], [0], None, [256], [0, 256])
            hist_sum = float(hist.sum()) if hist is not None else 0.0
            if hist_sum > 0:
                p = (hist / hist_sum).flatten()
                # Evitar log(0)
                p = p[p > 0]
                lbp_entropy = float(-(p * np.log2(p)).sum())
            else:
                lbp_entropy = 0.0

            entropy_score = min(lbp_entropy / 5.0, 1.0)

            # 3) Brillo especular (pantallas con reflejos)
            glare_ratio = float((gray > 245).mean())

            confidence = float((texture * 0.5) + (contrast_score * 0.2) + (entropy_score * 0.3))

            # ===== Detección de pantalla (frecuencia) =====
            # Fotos en pantallas suelen presentar picos de frecuencia periódicos
            try:
                f = np.fft.fft2(gray)
                fshift = np.fft.fftshift(f)
                magnitude = np.abs(fshift)
                h, w = magnitude.shape
                # Enmascarar bajas frecuencias (centro)
                cy, cx = h // 2, w // 2
                r = int(min(h, w) * 0.1)
                magnitude[cy - r:cy + r, cx - r:cx + r] = 0
                high_mean = float(magnitude.mean()) if magnitude.size else 0.0
                high_max = float(magnitude.max()) if magnitude.size else 0.0
                peak_ratio = (high_max / high_mean) if high_mean > 0 else 0.0

                # Energía de bajas frecuencias (pantallas/fotos tienden a ser dominantes en low-freq)
                magnitude_full = np.abs(fshift)
                low_r = int(min(h, w) * 0.15)
                low_mask = np.zeros_like(magnitude_full, dtype=np.uint8)
                cv2.circle(low_mask, (cx, cy), low_r, 1, -1)
                low_energy = float((magnitude_full * low_mask).sum())
                total_energy = float(magnitude_full.sum()) if magnitude_full.size else 1.0
                low_freq_ratio = low_energy / total_energy if total_energy > 0 else 1.0
            except Exception:
                peak_ratio = 0.0
                low_freq_ratio = 1.0

            # ===== Densidad de bordes (pantallas tienden a bordes más duros y uniformes) =====
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edge_mag = np.sqrt(sobelx**2 + sobely**2)
            edge_density = float((edge_mag > 20).mean())

            # Umbrales más estrictos para evitar spoofing en pantallas
            # ===== Modo Estricto =====
            # Reglas base más duras
            is_real = (
                (laplacian_var > 90) and
                (contrast > 35) and
                (lbp_entropy > 4.8) and
                (edge_density > 0.07) and
                (edge_density < 0.22) and
                (glare_ratio < 0.04) and
                (low_freq_ratio < 0.88) and
                (peak_ratio < 30)
            )

            # Reglas de rechazo inmediato
            if glare_ratio > 0.04:
                is_real = False
            if peak_ratio >= 30:
                is_real = False
            if low_freq_ratio >= 0.88:
                is_real = False
            if laplacian_var < 90 or contrast < 35 or lbp_entropy < 4.8:
                is_real = False

            if is_real:
                return True, confidence, "Rostro real"
            return False, confidence, "Posible spoofing (pantalla/foto)"
            
        except Exception as e:
            logger.error(f"Error anti-spoofing: {e}")
            # Fail-safe: si no se puede verificar, se rechaza
            return False, 0.0, "No verificado"
    
    def verify_face_with_antispoofing(self,
                                      image_data: bytes,
                                      stored_encoding: List[float],
                                      threshold: float = None) -> Tuple[bool, dict, str]:
        """Verificación completa: anti-spoofing + reconocimiento."""
        threshold = threshold or self._threshold
        
        is_real, spoof_conf, spoof_msg = self.detect_spoofing(image_data)
        
        if not is_real:
            return False, {
                'is_real': False,
                'spoof_confidence': float(spoof_conf),
                'face_match': False,
                'distance': 1.0
            }, f"Denegado: {spoof_msg}"
        
        face_match, distance, face_msg = self.verify_face(
            image_data, stored_encoding, threshold
        )
        
        return face_match, {
            'is_real': True,
            'spoof_confidence': float(spoof_conf),
            'face_match': face_match,
            'distance': float(distance)
        }, face_msg
    
    def verify_face_encoding(self,
                             new_encoding: List[float],
                             stored_encoding: List[float],
                             threshold: float = None) -> Tuple[bool, float, str]:
        """
        Compara dos encodings faciales directamente sin necesidad de imagen.
        Usado para verificar si un rostro ya existe en otra cuenta.
        
        Args:
            new_encoding: Encoding del nuevo rostro
            stored_encoding: Encoding almacenado en BD
            threshold: Umbral de distancia (menor = más estricto)
            
        Returns:
            Tuple[is_match, similarity, message]
        """
        threshold = threshold or 0.30
        
        try:
            current = np.array(new_encoding, dtype=np.float32)
            stored = np.array(stored_encoding, dtype=np.float32)
            
            # Verificar compatibilidad de dimensiones
            if len(current) != len(stored):
                return False, 0.0, "Dimensiones incompatibles"
            
            if self._use_dnn and len(current) == 128:
                # Usar métricas de SFace para embeddings de 128D
                current_2d = current.reshape(1, -1)
                stored_2d = stored.reshape(1, -1)
                
                # Similitud coseno
                cosine_score = self._recognizer.match(
                    current_2d, stored_2d, 
                    cv2.FaceRecognizerSF_FR_COSINE
                )
                
                # Distancia L2 normalizada
                l2_score = self._recognizer.match(
                    current_2d, stored_2d,
                    cv2.FaceRecognizerSF_FR_NORM_L2
                )
                
                l2_similarity = max(0, 1 - l2_score / 2)
                combined = (cosine_score * 0.7 + l2_similarity * 0.3)
                
                MIN_COSINE = 0.35  # Umbral de SFace
                
                is_match = cosine_score >= MIN_COSINE and (1 - combined) < threshold
                
                logger.debug(f"Comparación encoding: coseno={cosine_score:.3f}, combinado={combined:.3f}")
                
                return is_match, float(combined), f"Similitud: {combined*100:.0f}%"
                
            else:
                # Fallback: similitud coseno manual
                norm_c = np.linalg.norm(current)
                norm_s = np.linalg.norm(stored)
                
                if norm_c > 0 and norm_s > 0:
                    cosine = float(np.dot(current, stored) / (norm_c * norm_s))
                else:
                    cosine = 0.0
                
                is_match = cosine >= 0.90  # 90% para LBP
                
                return is_match, cosine, f"Similitud: {cosine*100:.0f}%"
                
        except Exception as e:
            logger.error(f"Error comparando encodings: {e}")
            return False, 0.0, f"Error: {str(e)}"


# Aliases para compatibilidad
DeepFaceService = OpenCVDNNFaceService
OpenCVFaceService = OpenCVDNNFaceService
MediaPipeFaceService = OpenCVDNNFaceService