'use client';

import React, { useCallback } from 'react';
import Webcam from 'react-webcam';
import { Button } from './ui/Button';
import { useCamera, videoConstraints } from '@/hooks/useCamera';

interface CameraProps {
    onCapture: (imageData: string) => void;
    onError?: (error: string) => void;
}

export function Camera({ onCapture, onError }: CameraProps) {
    const { webcamRef, imageSrc, isCapturing, error, capture, retake } = useCamera();

    const handleCapture = useCallback(() => {
        capture();
    }, [capture]);

    const handleConfirm = useCallback(() => {
        if (imageSrc) {
            onCapture(imageSrc);
        }
    }, [imageSrc, onCapture]);

    const handleRetake = useCallback(() => {
        retake();
    }, [retake]);

    React.useEffect(() => {
        if (error && onError) {
            onError(error);
        }
    }, [error, onError]);

    return (
        <div className="relative w-full max-w-md mx-auto">
            {/* Camera container with gradient border */}
            <div className="relative p-1 rounded-2xl bg-gradient-to-r from-violet-500 to-indigo-500">
                <div className="relative overflow-hidden rounded-xl bg-gray-900">
                    {imageSrc ? (
                        // Show captured image
                        <img
                            src={imageSrc}
                            alt="Captured"
                            className="w-full aspect-[4/3] object-cover"
                        />
                    ) : (
                        // Show live webcam feed
                        <Webcam
                            ref={webcamRef}
                            audio={false}
                            screenshotFormat="image/jpeg"
                            videoConstraints={videoConstraints}
                            className="w-full aspect-[4/3] object-cover"
                            mirrored={true}
                        />
                    )}

                    {/* Face guide overlay */}
                    {!imageSrc && (
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="w-48 h-60 border-2 border-dashed border-violet-400/50 rounded-full" />
                        </div>
                    )}

                    {/* Status indicator */}
                    <div className="absolute top-4 left-4 flex items-center space-x-2">
                        <div
                            className={`w-3 h-3 rounded-full ${imageSrc ? 'bg-green-500' : 'bg-red-500 animate-pulse'
                                }`}
                        />
                        <span className="text-xs text-white/80 font-medium">
                            {imageSrc ? 'Capturado' : 'En vivo'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Instructions */}
            <p className="mt-4 text-center text-sm text-gray-400">
                {imageSrc
                    ? 'Revise la imagen y confirme o vuelva a intentar'
                    : 'Coloque su rostro dentro del círculo y capture la imagen'}
            </p>

            {/* Action buttons */}
            <div className="mt-6 flex justify-center space-x-4">
                {imageSrc ? (
                    <>
                        <Button variant="secondary" onClick={handleRetake}>
                            Reintentar
                        </Button>
                        <Button onClick={handleConfirm}>
                            Confirmar
                        </Button>
                    </>
                ) : (
                    <Button
                        onClick={handleCapture}
                        isLoading={isCapturing}
                        className="w-full"
                    >
                        <svg
                            className="w-5 h-5 mr-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                            />
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                        </svg>
                        Capturar Foto
                    </Button>
                )}
            </div>

            {/* Error message */}
            {error && (
                <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                    <p className="text-sm text-red-400 text-center">{error}</p>
                </div>
            )}
        </div>
    );
}
