"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, Play, Download } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Log {
  message: string;
  timestamp: Date;
  type: "info" | "success" | "error";
}

interface SearchResults {
  csvUrl?: string;
  message?: string;
  error?: string;
}

export function JobSearchDashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<Log[]>([]);
  const [results, setResults] = useState<SearchResults | null>(null);

  function addLog(message: string, type: Log["type"] = "info") {
    setLogs(prev => [...prev, {
      message,
      timestamp: new Date(),
      type,
    }]);
  }

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const uploadedFile = event.target.files?.[0];
    if (!uploadedFile) return;

    if (!uploadedFile.name.toLowerCase().endsWith('.pdf')) {
      addLog('Solo se permiten archivos PDF', 'error');
      return;
    }

    setFile(uploadedFile);
    addLog(`CV cargado: ${uploadedFile.name}`, 'success');
  }

  async function startProcessing() {
    if (!file) {
      addLog('Por favor, sube un CV primero', 'error');
      return;
    }

    setIsProcessing(true);
    addLog('Iniciando búsqueda de trabajos...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      addLog('Analizando CV...');
      const response = await fetch('/api/process-cv', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Error al procesar el CV');
      }

      if (data.message) {
        addLog(data.message, 'success');
      }

      setResults(data);
      addLog('¡Búsqueda completada!', 'success');
    } catch (error) {
      addLog(error instanceof Error ? error.message : 'Error en el proceso', 'error');
    } finally {
      setIsProcessing(false);
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardContent className="p-6 space-y-6">
          <div className="text-center">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
              id="cv-upload"
              disabled={isProcessing}
            />
            <label htmlFor="cv-upload">
              <Button 
                variant="outline" 
                className="w-full mb-4"
                disabled={isProcessing}
                asChild
              >
                <span>
                  <Upload className="mr-2 h-4 w-4" />
                  {file ? 'Cambiar CV' : 'Subir CV'}
                </span>
              </Button>
            </label>
            {file && (
              <p className="text-sm text-muted-foreground">
                {file.name}
              </p>
            )}
          </div>

          <Button 
            onClick={startProcessing}
            disabled={!file || isProcessing}
            className="w-full"
          >
            <Play className="mr-2 h-4 w-4" />
            {isProcessing ? 'Procesando...' : 'Iniciar Búsqueda'}
          </Button>

          {results && (
            <div className="space-y-3">
              {results.csvUrl && (
                <Button
                  variant="outline"
                  className="w-full"
                  asChild
                >
                  <a href={results.csvUrl} download="job-results.csv">
                    <Download className="mr-2 h-4 w-4" />
                    Descargar Resultados (CSV)
                  </a>
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h3 className="font-medium mb-4">Registro de Actividad</h3>
          <ScrollArea className="h-[400px] rounded-md border p-4">
            <div className="space-y-3">
              {logs.map((log, index) => (
                <div 
                  key={index}
                  className={`text-sm p-2 rounded ${
                    log.type === 'error' ? 'bg-red-100 text-red-800' :
                    log.type === 'success' ? 'bg-green-100 text-green-800' :
                    'bg-blue-100 text-blue-800'
                  }`}
                >
                  <p>{log.message}</p>
                  <p className="text-xs opacity-70">
                    {log.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
} 