import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { useWallet } from '../contexts/WalletContext';
import { AnalysisResult } from '../components/AnalysisResult';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from '../components/ui/sonner';

export default function ChapterResult() {
  const { analysisRunId } = useParams();
  const { t } = useTranslation();
  const { refresh } = useWallet();
  const [analysis, setAnalysis] = useState(null);
  const [chapter, setChapter] = useState(null);
  const [estimate, setEstimate] = useState(null);
  const [criticalLoading, setCriticalLoading] = useState(false);

  const load = async () => {
    const { data } = await api.get(`/analysis_runs/${analysisRunId}`);
    setAnalysis(data);
    const { data: ch } = await api.get(`/chapters/${data.chapter_id}`);
    setChapter(ch);
    if (!data.leitura_critica_executada) {
      const { data: est } = await api.get(`/chapters/${data.chapter_id}/estimate`);
      setEstimate(est);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysisRunId]);

  const handleRunCritical = async () => {
    setCriticalLoading(true);
    try {
      const { data } = await api.post(`/analysis_runs/${analysisRunId}/critical_reading`);
      setAnalysis((prev) => ({
        ...prev,
        leitura_critica: data.leitura_critica,
        leitura_critica_executada: true,
        creditos_consumidos: data.creditos_consumidos,
      }));
      await refresh();
    } catch (err) {
      if (err.response?.status === 402) {
        toast.error('Saldo de créditos insuficiente para a Leitura Crítica.');
      } else {
        toast.error('Erro ao rodar a Leitura Crítica.');
      }
    } finally {
      setCriticalLoading(false);
    }
  };

  const buildChapterText = (suffix) => (
    <div className="rounded-xl border border-white/5 bg-[#121215] p-6" data-testid={`chapter-text-panel-${suffix}`}>
      <h2 className="font-medium text-[#F4F4F5] mb-4">{chapter?.titulo}</h2>
      <div
        className="whitespace-pre-wrap leading-relaxed text-[#E6E4DD] max-w-3xl"
        style={{ fontFamily: 'Lora, serif', fontSize: '1.05rem' }}
        data-testid={`chapter-text-content-${suffix}`}
      >
        {chapter?.texto_bruto}
      </div>
    </div>
  );

  const buildResultsPanel = (suffix) => (
    <div data-testid={`results-panel-${suffix}`}>
      <AnalysisResult
        analysis={analysis}
        idSuffix={suffix}
        onRunCritical={handleRunCritical}
        criticalLoading={criticalLoading}
        criticalEstimate={estimate}
      />
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10" data-testid="chapter-result-page">
      <Link to="/dashboard" className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200" data-testid="back-to-dashboard-link">
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>

      <div className="hidden lg:grid grid-cols-12 gap-8">
        <div className="col-span-7">{buildChapterText('desktop')}</div>
        <div className="col-span-5">{buildResultsPanel('desktop')}</div>
      </div>

      <div className="lg:hidden">
        <Tabs defaultValue="texto">
          <TabsList data-testid="mobile-result-tabs">
            <TabsTrigger value="texto" data-testid="mobile-tab-texto">Capítulo</TabsTrigger>
            <TabsTrigger value="analise" data-testid="mobile-tab-analise">Análise</TabsTrigger>
          </TabsList>
          <TabsContent value="texto" className="mt-4">{buildChapterText('mobile')}</TabsContent>
          <TabsContent value="analise" className="mt-4">{buildResultsPanel('mobile')}</TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
