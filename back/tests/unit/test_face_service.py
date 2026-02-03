"""
Login Seguro - Tests Unitarios: OpenCV DNN Face Service
Tests para el servicio de reconocimiento facial
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import base64

from app.infrastructure.services.deepface_service import OpenCVDNNFaceService


class TestOpenCVDNNFaceService:
    """Tests para OpenCVDNNFaceService"""
    
    @pytest.fixture
    def mock_cv2(self):
        """Mock de cv2"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock:
            mock.data.haarcascades = ''
            mock.CascadeClassifier.return_value = MagicMock()
            yield mock
    
    @pytest.fixture
    def sample_image_base64(self):
        """Imagen de prueba en base64"""
        # Crear imagen de prueba (10x10 píxeles negros)
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        import cv2
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')
    
    @pytest.fixture
    def sample_image_with_prefix(self, sample_image_base64):
        """Imagen con prefijo MIME"""
        return f"data:image/jpeg;base64,{sample_image_base64}"
    
    def test_decode_image_valid_base64(self, sample_image_base64):
        """Test decodificación de imagen base64 válida"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            mock_cv2.imdecode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            
            service = OpenCVDNNFaceService()
            img = service._decode_image(sample_image_base64)
            
            assert img is not None
    
    def test_decode_image_with_mime_prefix(self, sample_image_with_prefix):
        """Test decodificación de imagen con prefijo MIME"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            mock_cv2.imdecode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            
            service = OpenCVDNNFaceService()
            img = service._decode_image(sample_image_with_prefix)
            
            assert img is not None
    
    def test_decode_image_invalid_data_raises_error(self):
        """Test que datos inválidos lanzan error"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            mock_cv2.imdecode.return_value = None  # Simular fallo
            
            service = OpenCVDNNFaceService()
            
            with pytest.raises(ValueError):
                service._decode_image("invalid_base64_data")
    
    def test_extract_face_encoding_returns_tuple(self, sample_image_base64):
        """Test que extract_face_encoding retorna tupla"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            mock_cv2.imdecode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
            
            cascade_mock = MagicMock()
            cascade_mock.detectMultiScale.return_value = np.array([[10, 10, 50, 50]])
            mock_cv2.CascadeClassifier.return_value = cascade_mock
            
            service = OpenCVDNNFaceService()
            result = service.extract_face_encoding(sample_image_base64)
            
            assert isinstance(result, tuple)
            assert len(result) == 3
    
    def test_verify_face_returns_tuple(self, sample_image_base64):
        """Test que verify_face retorna tupla"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            mock_cv2.imdecode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
            
            service = OpenCVDNNFaceService()
            stored_encoding = [0.1] * 128
            
            result = service.verify_face(sample_image_base64, stored_encoding)
            
            assert isinstance(result, tuple)
            assert len(result) == 3
    
    def test_detect_spoofing_returns_tuple(self, sample_image_base64):
        """Test que detect_spoofing retorna tupla"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            mock_cv2.imdecode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_cv2.Laplacian.return_value = np.ones((100, 100), dtype=np.float32)
            
            service = OpenCVDNNFaceService()
            
            result = service.detect_spoofing(sample_image_base64)
            
            assert isinstance(result, tuple)
            assert len(result) == 3
    
    def test_verify_face_with_antispoofing_returns_tuple(self, sample_image_base64):
        """Test que verify_face_with_antispoofing retorna tupla"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            mock_cv2.imdecode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_cv2.Laplacian.return_value = np.ones((100, 100), dtype=np.float32)
            
            cascade_mock = MagicMock()
            cascade_mock.detectMultiScale.return_value = np.array([[10, 10, 50, 50]])
            mock_cv2.CascadeClassifier.return_value = cascade_mock
            
            service = OpenCVDNNFaceService()
            stored_encoding = [0.1] * 128
            
            result = service.verify_face_with_antispoofing(sample_image_base64, stored_encoding)
            
            assert isinstance(result, tuple)
            assert len(result) == 3


class TestFaceServiceInterface:
    """Tests para verificar cumplimiento de la interfaz"""
    
    def test_implements_interface(self):
        """Test que implementa IFaceService"""
        from app.domain.interfaces.face_service import IFaceService
        
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            
            service = OpenCVDNNFaceService()
            
            assert isinstance(service, IFaceService)
    
    def test_has_required_methods(self):
        """Test que tiene los métodos requeridos"""
        with patch('app.infrastructure.services.deepface_service.cv2') as mock_cv2:
            mock_cv2.data.haarcascades = ''
            mock_cv2.CascadeClassifier.return_value = MagicMock()
            
            service = OpenCVDNNFaceService()
            
            assert hasattr(service, 'extract_face_encoding')
            assert hasattr(service, 'verify_face')
            assert hasattr(service, 'detect_spoofing')
            assert hasattr(service, 'verify_face_with_antispoofing')
            assert callable(service.extract_face_encoding)
            assert callable(service.verify_face)
            assert callable(service.detect_spoofing)
            assert callable(service.verify_face_with_antispoofing)
