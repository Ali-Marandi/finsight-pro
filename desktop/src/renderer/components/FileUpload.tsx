import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileSpreadsheet } from 'lucide-react';
import { cn } from '../lib/utils';

interface FileUploadProps {
  onFileSelected: (filePath: string) => void;
  isLoading?: boolean;
}

export default function FileUpload({ onFileSelected, isLoading = false }: FileUploadProps) {
  const handleElectronFile = async () => {
    if (window.electronAPI) {
      const filePath = await window.electronAPI.openFile();
      if (filePath) onFileSelected(filePath);
    }
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      // In Electron, use the file path. In browser, create object URL.
      const path = (file as unknown as { path: string }).path || URL.createObjectURL(file);
      onFileSelected(path);
    }
  }, [onFileSelected]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/pdf': ['.pdf'],
    },
    multiple: false,
  });

  return (
    <div className="space-y-4">
      {/* Drop zone (for drag & drop) */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200',
          isDragActive
            ? 'border-cascade-gold bg-cascade-gold/5'
            : 'border-cascade-mist hover:border-cascade-sage hover:bg-cascade-soft-white',
          isLoading && 'pointer-events-none opacity-50'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-cascade-gold/10 flex items-center justify-center">
            {isDragActive ? (
              <FileSpreadsheet size={32} className="text-cascade-gold" />
            ) : (
              <Upload size={32} className="text-cascade-gold" />
            )}
          </div>
          <div>
            <p className="text-base font-semibold text-cascade-charcoal">
              {isDragActive ? 'Drop your file here' : 'Drag & drop a financial statement'}
            </p>
            <p className="text-sm text-cascade-sage mt-1">
              or click to browse • CSV, XLS, XLSX, PDF
            </p>
          </div>
        </div>
      </div>

      {/* Electron native file picker button */}
      {window.electronAPI && (
        <button
          onClick={handleElectronFile}
          disabled={isLoading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          <FileSpreadsheet size={16} />
          {isLoading ? 'Analyzing…' : 'Browse Files (Native)'}
        </button>
      )}
    </div>
  );
}
