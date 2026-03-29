"use client";

import { useState, useCallback, useRef } from "react";
import { cn } from "@/lib/utils";
import {
  Upload,
  FileSpreadsheet,
  X,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { uploadFile, UploadResult } from "@/lib/api";

interface FileUploadProps {
  onFileUploaded: (result: UploadResult) => void;
  onFileRemoved: () => void;
  uploadedFile: UploadResult | null;
  disabled?: boolean;
  className?: string;
}

export function FileUpload({
  onFileUploaded,
  onFileRemoved,
  uploadedFile,
  disabled = false,
  className,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ACCEPTED_TYPES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
  ];
  const ACCEPTED_EXTENSIONS = [".xlsx", ".xls", ".csv"];

  const validateFile = (file: File): boolean => {
    const ext = file.name.toLowerCase().slice(file.name.lastIndexOf("."));
    if (
      !ACCEPTED_EXTENSIONS.includes(ext) &&
      !ACCEPTED_TYPES.includes(file.type)
    ) {
      setError("Please upload an Excel (.xlsx, .xls) or CSV (.csv) file");
      return false;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError("File size must be under 50MB");
      return false;
    }
    return true;
  };

  const handleUpload = useCallback(
    async (file: File) => {
      if (!validateFile(file)) return;
      setError(null);
      setIsUploading(true);
      try {
        const result = await uploadFile(file);
        onFileUploaded(result);
      } catch (err) {
        setError((err as Error).message || "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [onFileUploaded],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled || isUploading) return;
      const file = e.dataTransfer.files[0];
      if (file) handleUpload(file);
    },
    [disabled, isUploading, handleUpload],
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled && !isUploading) setIsDragging(true);
    },
    [disabled, isUploading],
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleClick = () => {
    if (!disabled && !isUploading) fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    e.target.value = "";
  };

  // Sleek glassmorphic card when file is already uploaded
  if (uploadedFile) {
    return (
      <div className={cn("w-full transition-all duration-300 animate-in fade-in zoom-in-95", className)}>
        <div className="relative overflow-hidden flex items-center justify-between p-4 rounded-2xl border border-emerald-500/30 bg-gradient-to-r from-emerald-500/10 to-emerald-400/5 shadow-lg shadow-emerald-500/10 group">
          {/* Subtle ambient glow behind card */}
          <div className="absolute -inset-10 bg-emerald-400/10 blur-3xl rounded-full -z-10 opacity-50 transition-opacity group-hover:opacity-100" />

          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/20">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-foreground truncate max-w-[200px] sm:max-w-[280px]">
                {uploadedFile.filename}
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-[11px] text-emerald-500 font-medium tracking-wide uppercase">Ready for analysis</span>
              </div>
            </div>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onFileRemoved();
            }}
            className="flex items-center justify-center w-8 h-8 rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors disabled:opacity-50"
            disabled={disabled}
            aria-label="Remove file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)}>
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
        className={cn(
          "relative overflow-hidden flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed p-10 cursor-pointer transition-all duration-300 group",
          isDragging
            ? "border-primary/60 bg-primary/10 scale-[1.02] shadow-xl shadow-primary/10"
            : "border-border/40 bg-muted/10 hover:border-primary/40 hover:bg-muted/30 hover:shadow-lg hover:shadow-primary/5",
          (disabled || isUploading) && "opacity-50 cursor-not-allowed",
          error && "border-destructive/50 bg-destructive/5",
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={handleFileChange}
          className="hidden"
          disabled={disabled || isUploading}
        />

        {isUploading ? (
          <>
            <div className="relative">
              <div className="absolute inset-0 blur-xl bg-primary/30 rounded-full animate-pulse" />
              <Loader2 className="relative h-10 w-10 text-primary animate-spin" />
            </div>
            <p className="text-sm font-medium text-primary animate-pulse mt-2">Uploading and analyzing...</p>
          </>
        ) : (
          <>
            <div className="relative">
              {/* Glowing orb effect behind the icon */}
              <div className="absolute inset-0 bg-primary/20 blur-2xl rounded-full scale-150 transition-transform duration-500 group-hover:scale-[2.0] group-hover:bg-primary/30" />
              <div className="relative flex items-center justify-center h-14 w-14 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20 shadow-inner transition-transform duration-300 group-hover:-translate-y-1">
                <Upload className="h-6 w-6 text-primary transition-colors duration-300 group-hover:text-primary" />
              </div>
            </div>
            <div className="text-center z-10">
              <p className="text-base font-medium text-foreground/90 tracking-tight transition-colors group-hover:text-foreground">
                <span className="hidden sm:inline">Drag & drop your file here, or </span>
                <span className="text-primary cursor-pointer hover:underline underline-offset-4">browse</span>
              </p>
              <p className="text-xs text-muted-foreground/80 mt-1.5 font-medium">
                Excel (.xlsx, .xls) and CSV up to 50MB
              </p>
            </div>
          </>
        )}
      </div>

      {error && (
        <p className="mt-2 text-xs text-destructive animate-in fade-in slide-in-from-top-1">
          {error}
        </p>
      )}
    </div>
  );
}
