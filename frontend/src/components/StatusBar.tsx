import React, { useState, useEffect } from 'react';
import { Server, Wifi, WifiOff, Activity, CheckCircle, XCircle } from 'lucide-react';
import { checkMediaPipeHealth, checkLLMHealth } from '../services/api';

interface ServiceStatus {
  name: string;
  isUp: boolean;
  isChecking: boolean;
}

export const StatusBar: React.FC = () => {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'MediaPipe', isUp: false, isChecking: true },
    { name: 'LLM Service', isUp: false, isChecking: true },
  ]);

  useEffect(() => {
    const checkServices = async () => {
      // Check MediaPipe
      try {
        await checkMediaPipeHealth();
        setServices((prev) =>
          prev.map((s) => (s.name === 'MediaPipe' ? { ...s, isUp: true, isChecking: false } : s))
        );
      } catch {
        setServices((prev) =>
          prev.map((s) => (s.name === 'MediaPipe' ? { ...s, isUp: false, isChecking: false } : s))
        );
      }

      // Check LLM
      try {
        await checkLLMHealth();
        setServices((prev) =>
          prev.map((s) => (s.name === 'LLM Service' ? { ...s, isUp: true, isChecking: false } : s))
        );
      } catch {
        setServices((prev) =>
          prev.map((s) => (s.name === 'LLM Service' ? { ...s, isUp: false, isChecking: false } : s))
        );
      }
    };

    checkServices();
    const interval = setInterval(checkServices, 10000); // Check every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const allUp = services.every((s) => s.isUp);

  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Title */}
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-blue-600" />
          <span className="font-semibold text-gray-800">Service Status</span>
        </div>

        {/* Service Indicators */}
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
              <span className={`text-sm ${service.isUp ? 'text-green-700' : 'text-red-700'}`}>
                {service.name}
              </span>
            </div>
          ))}
        </div>

        {/* Overall Status */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100">
          {allUp ? (
            <>
              <Wifi className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium text-green-700">All Services Ready</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-red-500" />
              <span className="text-sm font-medium text-red-700">Some Services Down</span>
            </>
          )}
        </div>
      </div>

      {/* Ports Info */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex gap-6 text-xs text-gray-500">
        <span>MediaPipe: localhost:8001</span>
        <span>LLM Service: localhost:8002</span>
        <span>WebSocket: ws://localhost:8001/ws/sign-detection</span>
      </div>
    </div>
  );
};
