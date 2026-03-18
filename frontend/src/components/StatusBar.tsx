import React, { useEffect, useState } from 'react';
import {
  Activity,
  CheckCircle,
  Server,
  Wifi,
  WifiOff,
  XCircle,
} from 'lucide-react';
import { checkLLMHealth, checkMediaPipeHealth } from '../services/api';

interface ServiceStatus {
  name: string;
  isUp: boolean;
  isChecking: boolean;
}

interface StatusBarProps {
  detectionGuidance: string | null;
  frameQuality: number;
}

function getReadinessTone(frameQuality: number) {
  if (frameQuality >= 0.85) {
    return {
      label: 'Recognition strong',
      className: 'bg-green-100 text-green-700',
    };
  }

  if (frameQuality >= 0.55) {
    return {
      label: 'Recognition warming up',
      className: 'bg-amber-100 text-amber-700',
    };
  }

  return {
    label: 'Recognition needs adjustment',
    className: 'bg-slate-100 text-slate-700',
  };
}

export const StatusBar: React.FC<StatusBarProps> = ({
  detectionGuidance,
  frameQuality,
}) => {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'MediaPipe', isUp: false, isChecking: true },
    { name: 'LLM Service', isUp: false, isChecking: true },
  ]);

  useEffect(() => {
    const checkServices = async () => {
      try {
        await checkMediaPipeHealth();
        setServices((prev) =>
          prev.map((service) =>
            service.name === 'MediaPipe'
              ? { ...service, isUp: true, isChecking: false }
              : service
          )
        );
      } catch {
        setServices((prev) =>
          prev.map((service) =>
            service.name === 'MediaPipe'
              ? { ...service, isUp: false, isChecking: false }
              : service
          )
        );
      }

      try {
        await checkLLMHealth();
        setServices((prev) =>
          prev.map((service) =>
            service.name === 'LLM Service'
              ? { ...service, isUp: true, isChecking: false }
              : service
          )
        );
      } catch {
        setServices((prev) =>
          prev.map((service) =>
            service.name === 'LLM Service'
              ? { ...service, isUp: false, isChecking: false }
              : service
          )
        );
      }
    };

    checkServices();
    const interval = setInterval(checkServices, 10000);

    return () => clearInterval(interval);
  }, []);

  const allUp = services.every((service) => service.isUp);
  const readiness = getReadinessTone(frameQuality);

  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-blue-600" />
          <span className="font-semibold text-gray-800">Service Status</span>
        </div>

        <div className="flex items-center gap-6">
          {services.map((service) => (
            <div key={service.name} className="flex items-center gap-2">
              {service.isChecking ? (
                <Activity className="w-4 h-4 text-gray-400 animate-pulse" />
              ) : service.isUp ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
              <span
                className={`text-sm ${
                  service.isUp ? 'text-green-700' : 'text-red-700'
                }`}
              >
                {service.name}
              </span>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100">
          {allUp ? (
            <>
              <Wifi className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium text-green-700">
                All Services Ready
              </span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-red-500" />
              <span className="text-sm font-medium text-red-700">
                Some Services Down
              </span>
            </>
          )}
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-100 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex gap-6 text-xs text-gray-500">
          <span>MediaPipe: localhost:8001</span>
          <span>LLM Service: localhost:8002</span>
          <span>WebSocket: ws://localhost:8001/ws/sign-detection</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${readiness.className}`}
          >
            {readiness.label}
          </span>
          <span className="text-xs text-gray-600">
            {detectionGuidance ?? 'Show one hand in the frame to start detection.'}
          </span>
        </div>
      </div>
    </div>
  );
};
