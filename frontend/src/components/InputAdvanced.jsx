import React, { useState, useRef } from 'react';
import { Paperclip, Send, FileText, X, BrainCircuit } from 'lucide-react';
import './InputAdvanced.css';

const InputAdvanced = ({ onSubmit, isLoading }) => {
  const [text, setText] = useState('');
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleTextChange = (e) => {
    setText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const handleFileChange = (e) => {
    const newFiles = Array.from(e.target.files);
    setFiles((prevFiles) => [...prevFiles, ...newFiles]);
  };

  const handleRemoveFile = (fileName) => {
    setFiles((prevFiles) => prevFiles.filter((file) => file.name !== fileName));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() === '' && files.length === 0) return;

    onSubmit(text, files);
    setText('');
    setFiles([]);
    // Reset textarea height
    const textarea = e.target.querySelector('textarea');
    if(textarea) textarea.style.height = 'auto';
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles((prevFiles) => [...prevFiles, ...droppedFiles]);
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div 
      className={`input-advanced-container ${isDragging ? 'dragging' : ''}`}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <form onSubmit={handleSubmit} className="input-advanced-form">
        {files.length > 0 && (
          <div className="file-preview-area">
            {files.map((file, index) => (
              <div key={index} className="file-chip">
                <FileText size={16} />
                <span>{file.name}</span>
                <button type="button" onClick={() => handleRemoveFile(file.name)}>
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="input-wrapper">
          <textarea
            value={text}
            onChange={handleTextChange}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu mensaje o arrastra una imagen aquí..."
            rows={1}
            disabled={isLoading}
          />
          <div className="button-group">
            <button
              type="button"
              className="icon-button"
              onClick={() => fileInputRef.current.click()}
              disabled={isLoading}
              title="Adjuntar archivo"
            >
              <Paperclip size={20} />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              style={{ display: 'none' }}
              multiple
            />
            <button 
              type="button" 
              className="icon-button"
              disabled // Deshabilitado por ahora, como placeholder para "Planes"
              title="Usar un plan (Próximamente)"
            >
              <BrainCircuit size={20} />
            </button>
            <button 
              type="submit" 
              className="send-button"
              disabled={isLoading || (text.trim() === '' && files.length === 0)}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default InputAdvanced;
