"""
Login Seguro - Interface del Servicio de Reconocimiento Facial
Define el contrato para el servicio de biometría facial
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional, List
import numpy as np


class IFaceService(ABC):
    """
    Interface para el servicio de reconocimiento facial.
    Permite cambiar la implementación (DeepFace, dlib, etc.) sin modificar el código cliente.
    """
    
    @abstractmethod
    def extract_face_encoding(self, image_data: bytes) -> Tuple[bool, Optional[List[float]], str]:
        """
        Extrae el encoding facial de una imagen.
        
        Args:
            image_data: Bytes de la imagen en formato base64 o raw
            
        Returns:
            Tuple[bool, Optional[List[float]], str]:
                - success: True si se extrajo correctamente
                - encoding: Lista de 128 floats con el encoding facial
                - message: Mensaje descriptivo del resultado
        """
        pass
    
    @abstractmethod
    def verify_face(self, 
                   image_data: bytes, 
                   stored_encoding: List[float],
                   threshold: float = 0.6) -> Tuple[bool, float, str]:
        """
        Verifica si el rostro en la imagen coincide con el encoding almacenado.
        
        Args:
            image_data: Bytes de la imagen a verificar
            stored_encoding: Encoding facial almacenado del usuario
            threshold: Umbral de similitud (menor = más estricto)
            
        Returns:
            Tuple[bool, float, str]:
                - match: True si hay coincidencia
                - distance: Distancia calculada entre rostros
                - message: Mensaje descriptivo
        """
        pass
    
    @abstractmethod
    def detect_spoofing(self, image_data: bytes) -> Tuple[bool, float, str]:
        """
        Detecta si la imagen es un intento de spoofing (foto, video, máscara).
        
        Args:
            image_data: Bytes de la imagen a analizar
            
        Returns:
            Tuple[bool, float, str]:
                - is_real: True si el rostro es real (no spoofing)
                - confidence: Nivel de confianza (0-1)
                - message: Mensaje descriptivo
        """
        pass
    
    @abstractmethod
    def verify_face_with_antispoofing(self,
                                      image_data: bytes,
                                      stored_encoding: List[float],
                                      threshold: float = 0.6) -> Tuple[bool, dict, str]:
        """
        Verificación completa: anti-spoofing + reconocimiento facial.
        
        Args:
            image_data: Bytes de la imagen
            stored_encoding: Encoding almacenado
            threshold: Umbral de similitud
            
        Returns:
            Tuple[bool, dict, str]:
                - success: True si pasa todas las verificaciones
                - details: Diccionario con detalles (is_real, distance, confidence)
                - message: Mensaje descriptivo
        """
        pass
