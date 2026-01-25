'use client';

import { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';

interface UseCameraReturn {
    webcamRef: React.RefObject<Webcam | null>;
    imageSrc: string | null;
    isCapturing: boolean;
    error: string | null;
    capture: () => void;
    retake: () => void;
    getBase64Image: () => string | null;
}

const videoConstraints = {
    width: 640,
    height: 480,
    facingMode: 'user',
};

export function useCamera(): UseCameraReturn {
    const webcamRef = useRef<Webcam>(null);
    const [imageSrc, setImageSrc] = useState<string | null>(null);
    const [isCapturing, setIsCapturing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const capture = useCallback(() => {
        setError(null);
        setIsCapturing(true);

        try {
            if (webcamRef.current) {
                const screenshot = webcamRef.current.getScreenshot();

                if (screenshot) {
                    setImageSrc(screenshot);
                } else {
                    setError('No se pudo capturar la imagen. Asegúrese de que la cámara esté activa.');
                }
            } else {
                setError('La cámara no está disponible.');
            }
        } catch (err) {
            setError('Error al capturar imagen: ' + (err instanceof Error ? err.message : 'Error desconocido'));
        } finally {
            setIsCapturing(false);
        }
    }, []);

    const retake = useCallback(() => {
        setImageSrc(null);
        setError(null);
    }, []);

    const getBase64Image = useCallback((): string | null => {
        return imageSrc;
    }, [imageSrc]);

    return {
        webcamRef,
        imageSrc,
        isCapturing,
        error,
        capture,
        retake,
        getBase64Image,
    };
}

export { videoConstraints };
