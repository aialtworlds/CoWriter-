import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { useWallet } from '../contexts/WalletContext';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { ChapterUpload } from '../components/ChapterUpload';
import { AnalysisConfirmModal } from '../components/AnalysisConfirmModal';
import { toast } from '../components/ui/sonner';

export default function ChapterNew() {
  const { projectId } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { refresh } = useWallet();
  const [titulo, setTitulo] = useState('');
  const [texto, setTexto] = useState('');
  const [chapterId, setChapterId] = useState(null);
  const [estimate, setEstimate] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [includeCritical, setIncludeCritical] = useState(true);
  const [explanationLanguage, setExplanationLanguage] = useState('');

  const wordCount = texto.trim() ? texto.trim().split(/\s+/).length : 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!texto.trim()) {
      toast.error(t('chapter.paste_text'));
      return;
    }
    setLoading(true);
    try {
      const { data: chapter } = await api.post(`/projects/${projectId}/chapters`, { titulo, texto_bruto: texto });
      setChapterId(chapter.id);
      const { data: est } = await api.get(`/chapters/${chapter.id}/estimate`);
      setEstimate(est);
      setModalOpen(true);
    } catch {
      toast.error('Erro ao salvar capítulo.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAnalyze = async () => {
    setLoading(true);
    try {
      const { data: analysis } = await api.post(
        `/chapters/${chapterId}/analyze`,
        null,
        {
          params: {
            incluir_leitura_critica: includeCritical,
            ...(explanationLanguage ? { idioma_explicacao: explanationLanguage } : {}),
          },
        },
      );
      await refresh();
      navigate(`/analysis/${analysis.analysis_run_id}`);
    } catch {
      toast.error('Erro ao analisar capítulo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10" data-testid="chapter-new-page">
      <Link to={`/projects/${projectId}`} className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200" data-testid="back-to-project-link">
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>
      <h1 className="text-2xl font-semibold tracking-tight text-[#F4F4F5] mb-6">{t('project.new_chapter')}</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          data-testid="chapter-title-input"
          placeholder={t('chapter.title_label')}
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          required
          className="bg-[#121215] border-white/10 text-[#E6E4DD]"
        />
        <ChapterUpload value={texto} onChange={setTexto} />
        <div className="flex items-center justify-between">
          <span className="text-sm text-[#9CA3AF]" data-testid="chapter-word-count">{t('chapter.word_count', { count: wordCount })}</span>
          <Button type="submit" data-testid="chapter-save-analyze-button" disabled={loading} className="bg-white text-black hover:bg-white/90 rounded-full">
            {loading ? t('chapter.analyzing') : t('chapter.save_and_analyze')}
          </Button>
        </div>
      </form>
      <AnalysisConfirmModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        estimate={estimate}
        onConfirm={handleConfirmAnalyze}
        loading={loading}
        includeCritical={includeCritical}
        onIncludeCriticalChange={setIncludeCritical}
        explanationLanguage={explanationLanguage}
        onExplanationLanguageChange={setExplanationLanguage}
      />
    </div>
  );
}
