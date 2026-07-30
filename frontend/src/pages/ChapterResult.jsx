import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { AnalysisResult } from '../components/AnalysisResult';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

export default function ChapterResult() {
  const { analysisRunId } = useParams();
  const { t } = useTranslation();
  const [analysis, setAnalysis] = useState(null);
  const [chapter, setChapter] = useState(null);

  useEffect(() => {
    api.get(`/analysis_runs/${analysisRunId}`).then(async ({ data }) => {
      setAnalysis(data);
      const { data: ch } = await api.get(`/chapters/${data.chapter_id}`);
      setChapter(ch);
    });
  }, [analysisRunId]);

  const ChapterText = (
    <div className="rounded-xl border border-white/5 bg-[#121215] p-6" data-testid="chapter-text-panel">
      <h2 className="font-medium text-[#F4F4F5] mb-4">{chapter?.titulo}</h2>
      <div
        className="whitespace-pre-wrap leading-relaxed text-[#E6E4DD] max-w-3xl"
        style={{ fontFamily: 'Lora, serif', fontSize: '1.05rem' }}
        data-testid="chapter-text-content"
      >
        {chapter?.texto_bruto}
      </div>
    </div>
  );

  const ResultsPanel = (
    <div data-testid="results-panel">
      <AnalysisResult analysis={analysis} />
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10" data-testid="chapter-result-page">
      <Link to="/dashboard" className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200" data-testid="back-to-dashboard-link">
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>

      <div className="hidden lg:grid grid-cols-12 gap-8">
        <div className="col-span-7">{ChapterText}</div>
        <div className="col-span-5">{ResultsPanel}</div>
      </div>

      <div className="lg:hidden">
        <Tabs defaultValue="texto">
          <TabsList data-testid="mobile-result-tabs">
            <TabsTrigger value="texto" data-testid="mobile-tab-texto">Capítulo</TabsTrigger>
            <TabsTrigger value="analise" data-testid="mobile-tab-analise">Análise</TabsTrigger>
          </TabsList>
          <TabsContent value="texto" className="mt-4">{ChapterText}</TabsContent>
          <TabsContent value="analise" className="mt-4">{ResultsPanel}</TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
