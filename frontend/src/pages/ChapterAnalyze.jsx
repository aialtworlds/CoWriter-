import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { useWallet } from '../contexts/WalletContext';
import { Button } from '../components/ui/button';
import { AnalysisConfirmModal } from '../components/AnalysisConfirmModal';
import { toast } from '../components/ui/sonner';

export default function ChapterAnalyze() {
  const { chapterId } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { refresh } = useWallet();
  const [chapter, setChapter] = useState(null);
  const [estimate, setEstimate] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [includeCritical, setIncludeCritical] = useState(true);
  const [explanationLanguage, setExplanationLanguage] = useState('');

  useEffect(() => {
    let mounted = true;
    Promise.all([
      api.get(`/chapters/${chapterId}`),
      api.get(`/chapters/${chapterId}/estimate`),
    ])
      .then(([{ data: ch }, { data: est }]) => {
        if (!mounted) return;
        setChapter(ch);
        setEstimate(est);
        setModalOpen(true);
      })
      .catch(() => {
        if (mounted) setError(true);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [chapterId]);

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
      setLoading(false);
    }
  };

  const backLink = chapter ? `/projects/${chapter.project_id}` : '/dashboard';

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10" data-testid="chapter-analyze-page">
      <Link to={backLink} className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200" data-testid="back-to-project-link">
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>

      {error && (
        <div className="text-center py-16" data-testid="chapter-analyze-error">
          <p className="text-[#E6E4DD] mb-4">Não foi possível carregar este capítulo. Ele pode ter sido excluído.</p>
          <Link to="/dashboard">
            <Button variant="outline" className="border-white/15 text-[#E6E4DD] hover:bg-white/5">
              {t('project.back_to_projects')}
            </Button>
          </Link>
        </div>
      )}

      {!error && chapter && (
        <>
          <h1 className="text-2xl font-semibold tracking-tight text-[#F4F4F5] mb-2">{chapter.titulo}</h1>
          <p className="text-sm text-[#9CA3AF] mb-6" data-testid="chapter-analyze-word-count">
            {t('chapter.word_count', { count: chapter.palavras })}
          </p>
        </>
      )}

      {!error && loading && !chapter && (
        <p className="text-[#9CA3AF]" data-testid="chapter-analyze-loading">{t('common.loading')}</p>
      )}

      <AnalysisConfirmModal
        open={modalOpen}
        onOpenChange={(open) => {
          setModalOpen(open);
          if (!open && !loading) navigate(backLink);
        }}
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
