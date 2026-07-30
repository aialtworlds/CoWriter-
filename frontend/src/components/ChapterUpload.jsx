import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import mammoth from 'mammoth';
import { UploadCloud } from 'lucide-react';
import { Textarea } from './ui/textarea';
import { toast } from './ui/sonner';

export function ChapterUpload({ value, onChange }) {
  const { t } = useTranslation();
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = async (file) => {
    if (!file) return;
    const name = file.name.toLowerCase();
    try {
      if (name.endsWith('.docx')) {
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        onChange(result.value);
      } else if (name.endsWith('.txt') || name.endsWith('.md')) {
        const text = await file.text();
        onChange(text);
      } else {
        toast.error('Formato não suportado. Use .docx, .txt ou .md.');
      }
    } catch (err) {
      toast.error('Não foi possível ler o arquivo.');
    }
  };

  return (
    <div className="space-y-3">
      <div
        data-testid="chapter-upload-dropzone"
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFile(e.dataTransfer.files?.[0]);
        }}
        onClick={() => inputRef.current?.click()}
        className={`flex items-center justify-center gap-2 rounded-lg border border-dashed p-4 text-sm cursor-pointer transition-colors duration-200 ${
          dragging ? 'border-emerald-400 bg-emerald-500/5 text-emerald-300' : 'border-white/15 text-[#9CA3AF] hover:border-white/30'
        }`}
      >
        <UploadCloud size={16} strokeWidth={1.5} />
        {t('chapter.drop_hint')}
        <input
          ref={inputRef}
          type="file"
          data-testid="chapter-upload-input"
          accept=".docx,.txt,.md"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
      <Textarea
        data-testid="chapter-text-textarea"
        placeholder={t('chapter.paste_text')}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-[300px] font-serif text-base leading-relaxed bg-[#121215] border-white/10 text-[#E6E4DD] resize-y"
        style={{ fontFamily: 'Lora, serif' }}
      />
    </div>
  );
}
