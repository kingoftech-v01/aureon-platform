/**
 * E-Signature Canvas Component
 * Aureon by Rhematek Solutions
 *
 * Allows users to draw their signature for contract signing
 */
import React, { useRef, useState, useCallback, useEffect } from 'react';

interface ESignatureCanvasProps {
  onSignatureChange: (signatureData: string | null) => void;
  width?: number;
  height?: number;
  penColor?: string;
  backgroundColor?: string;
}

const ESignatureCanvas: React.FC<ESignatureCanvasProps> = ({
  onSignatureChange,
  width = 500,
  height = 200,
  penColor = '#1e293b',
  backgroundColor = '#f8fafc',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = penColor;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, [width, height, penColor, backgroundColor]);

  const getPosition = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * (canvas.width / rect.width),
      y: (e.clientY - rect.top) * (canvas.height / rect.height),
    };
  }, []);

  const startDrawing = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const pos = getPosition(e);
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
    setIsDrawing(true);
  }, [getPosition]);

  const draw = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const pos = getPosition(e);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
    setHasSignature(true);
  }, [isDrawing, getPosition]);

  const stopDrawing = useCallback(() => {
    setIsDrawing(false);
    if (hasSignature) {
      const canvas = canvasRef.current;
      if (canvas) {
        onSignatureChange(canvas.toDataURL('image/png'));
      }
    }
  }, [hasSignature, onSignatureChange]);

  const clear = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, width, height);
    setHasSignature(false);
    onSignatureChange(null);
  }, [width, height, backgroundColor, onSignatureChange]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Draw your signature below
        </label>
        {hasSignature && (
          <button
            type="button"
            onClick={clear}
            className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 font-medium"
          >
            Clear
          </button>
        )}
      </div>
      <div className="relative border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl overflow-hidden hover:border-primary-400 dark:hover:border-primary-500 transition-colors">
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className="w-full cursor-crosshair"
          style={{ touchAction: 'none' }}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
        />
        {!hasSignature && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <p className="text-gray-400 dark:text-gray-500 text-sm">
              Sign here
            </p>
          </div>
        )}
        <div className="absolute bottom-3 left-4 right-4 border-b border-gray-300 dark:border-gray-600" />
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        By signing, you agree to the terms and conditions of this contract.
      </p>
    </div>
  );
};

export default ESignatureCanvas;
