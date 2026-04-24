import { useRef, useState } from "react";

export default function UploadCard({ title, accept, onUpload }) {
  const inputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFile = async (file) => {
    if (!file) return;
    setIsUploading(true);
    try {
      await onUpload(file);
      window.alert(`${title} upload successful`);
    } catch (error) {
      window.alert(error.message || `Failed to upload ${title.toLowerCase()}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div
      className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-6 shadow-soft"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 text-sm text-slate-500">Drag and drop a file here, or click to browse.</p>
      <button
        type="button"
        className="mt-4 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        onClick={() => inputRef.current?.click()}
        disabled={isUploading}
      >
        {isUploading ? "Uploading..." : "Select file"}
      </button>
      <input
        ref={inputRef}
        className="hidden"
        type="file"
        accept={accept}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
    </div>
  );
}
