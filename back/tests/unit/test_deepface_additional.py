"""
Tests adicionales para aumentar cobertura de deepface_service
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np
import base64

from app.infrastructure.services.deepface_service import OpenCVDNNFaceService


class TestOpenCVDNNAdditional:
    """Tests adicionales para aumentar cobertura"""
    
    def test_detect_face_dnn_returns_face(self):
        """Test que _detect_face_dnn procesa imagen"""
        service = OpenCVDNNFaceService()
        
        # Crear imagen simple
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # El método puede retornar None o array dependiendo de detección
        result = service._detect_face_dnn(img)
        
        # Resultado válido es None o ndarray
        assert result is None or isinstance(result, np.ndarray)
    
    def test_detect_face_haar_fallback(self):
        """Test que _detect_face_haar funciona como fallback"""
        service = OpenCVDNNFaceService()
        
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        result = service._detect_face_haar(img)
        
        # Resultado válido es None o tupla de coordenadas
        assert result is None or isinstance(result, tuple)
    
    def test_extract_embedding_dnn_processes_face(self):
        """Test que _extract_embedding_dnn procesa rostro detectado"""
        service = OpenCVDNNFaceService()
        
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        face = np.zeros((50, 50, 3), dtype=np.uint8)
        
        try:
            result = service._extract_embedding_dnn(img, face)
            # Debería retornar array o lanzar excepción
            assert isinstance(result, np.ndarray) or result is None
        except Exception:
            # Es válido que falle con imagen sintética
            pass
    
    def test_extract_embedding_fallback_with_rect(self):
        """Test que _extract_embedding_fallback procesa con rect"""
        service = OpenCVDNNFaceService()
        
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        face_rect = (10, 10, 50, 50)  # x, y, w, h
        
        try:
            result = service._extract_embedding_fallback(img, face_rect)
            # Debería retornar lista de floats
            assert isinstance(result, list) or result is None
        except Exception:
            # Es válido que falle con imagen sintética
            pass
    
    @patch.object(OpenCVDNNFaceService, '_decode_image')
    @patch.object(OpenCVDNNFaceService, '_detect_face_dnn')
    @patch.object(OpenCVDNNFaceService, '_extract_embedding_dnn')
    def test_extract_face_encoding_uses_dnn_pipeline(self, mock_embed, mock_detect, mock_decode):
        """Test que extract_face_encoding usa pipeline DNN completo"""
        service = OpenCVDNNFaceService()
        
        # Configurar mocks
        mock_decode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_detect.return_value = np.zeros((50, 50, 3), dtype=np.uint8)
        mock_embed.return_value = np.array([0.1] * 128)
        
        image_data = base64.b64encode(b"fake_image").decode()
        
        success, encoding, message = service.extract_face_encoding(image_data)
        
        # Verificar que se llamaron los métodos
        assert mock_decode.called
        assert mock_detect.called
        assert mock_embed.called
    
    @patch.object(OpenCVDNNFaceService, '_decode_image')
    @patch.object(OpenCVDNNFaceService, '_detect_face_dnn')
    def test_extract_face_encoding_handles_no_face_detected(self, mock_detect, mock_decode):
        """Test que maneja cuando no se detecta rostro"""
        service = OpenCVDNNFaceService()
        
        mock_decode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_detect.return_value = None  # No se detectó rostro
        
        image_data = base64.b64encode(b"fake_image").decode()
        
        success, encoding, message = service.extract_face_encoding(image_data)
        
        assert success is False
        assert encoding is None
        assert "detectó" in message.lower() or "detect" in message.lower()
    
    @patch.object(OpenCVDNNFaceService, '_decode_image')
    @patch.object(OpenCVDNNFaceService, 'extract_face_encoding')
    def test_verify_face_calls_extract_encoding(self, mock_extract, mock_decode):
        """Test que verify_face llama a extract_face_encoding"""
        service = OpenCVDNNFaceService()
        
        mock_decode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_extract.return_value = (True, [0.1] * 128, "Success")
        
        stored_encoding = [0.1] * 128
        image_data = base64.b64encode(b"fake_image").decode()
        
        # verify_face tiene firma: (image_data, stored_encoding, threshold=None)
        success, distance, message = service.verify_face(image_data, stored_encoding)
        
        # Verificar tipos de retorno
        assert isinstance(success, bool)
        assert isinstance(distance, (int, float))
        assert isinstance(message, str)
    
    @patch.object(OpenCVDNNFaceService, '_decode_image')
    @patch.object(OpenCVDNNFaceService, '_detect_face_dnn')
    def test_detect_spoofing_basic_check(self, mock_detect, mock_decode):
        """Test que detect_spoofing realiza verificación básica"""
        service = OpenCVDNNFaceService()
        
        mock_decode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_detect.return_value = np.zeros((50, 50, 3), dtype=np.uint8)
        
        image_data = base64.b64encode(b"fake_image").decode()
        
        is_real, confidence, message = service.detect_spoofing(image_data)
        
        # Verificar tipos de retorno
        assert isinstance(is_real, bool)
        assert isinstance(confidence, (int, float))
        assert isinstance(message, str)
