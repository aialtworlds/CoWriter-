import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Copy, CheckCircle2, AlertTriangle, Sparkles, Download, FileText } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { toast } from './ui/sonner';
import { api } from '../lib/api';

const SENSORY_CHANNEL_KEYS = {
  visual: 'sensory_visual',
  auditivo: 'sensory_auditory',
  olfativo: 'sensory_olfactory',
  tatil: 'sensory_tactile',
  gustativo: 'sensory_gustatory',
};

function DistributionBars({ distribuicao, labelFor, testId }) {
  if (!distribuicao) return null;
  const total = Object.values(distribuicao).reduce((a, b) => a + b, 0);
  if (total === 0) return null;
  return (
    <div className="space-y-1" data-testid={testId}>
      {Object.entries(distribuicao).map(([key, count]) => {
        const pct = total > 0 ? Math.round((count / total) * 100) : 0;
        return (
          <div key={key} className="flex items-center gap-2 text-xs">
            <span className="w-24 shrink-0 text-[#9CA3AF] truncate" title={labelFor ? labelFor(key) : key}>
              {labelFor ? labelFor(key) : key}
            </span>
            <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div className="h-full bg-emerald-400/70" style={{ width: `${pct}%` }} />
            </div>
            <span className="w-14 shrink-0 text-right text-[#6B7280]">{count} ({pct}%)</span>
          </div>
        );
      })}
    </div>
  );
}

function SensoryDistribution({ distribuicao }) {
  const { t } = useTranslation();
  if (!distribuicao) return null;
  const total = Object.values(distribuicao).reduce((a, b) => a + b, 0);
  if (total === 0) return null;
  return (
    <div className="space-y-1.5 pt-1" data-testid="sensory-distribution">
      <p className="text-[11px] uppercase tracking-wide text-[#6B7280]">
        {t('results.sensory_distribution_label')}
      </p>
      <DistributionBars
        distribuicao={distribuicao}
        labelFor={(channel) => t(`results.${SENSORY_CHANNEL_KEYS[channel] || channel}`)}
      />
    </div>
  );
}

function CheckMetrics({ check }) {
  const { t, i18n } = useTranslation();
  const m = check.metricas;
  if (!m) return null;
  const fmt = (n) => {
    try {
      return Number(n ?? 0).toLocaleString(i18n.language, { maximumFractionDigits: 1 });
    } catch {
      return String(Math.round((n ?? 0) * 10) / 10);
    }
  };

  switch (check.check_type) {
    case 'ai_fingerprint':
      return (
        <p className="text-xs text-[#6B7280]" data-testid={`check-metrics-${check.check_type}`}>
          {t('results.metrics_ai_fingerprint', { found: check.contagem, total: m.frases_monitoradas })}
        </p>
      );
    case 'filter_words':
      return (
        <p className="text-xs text-[#6B7280]" data-testid={`check-metrics-${check.check_type}`}>
          {t('results.metrics_filter_words', { found: check.contagem, total: m.frases_monitoradas })}
        </p>
      );
    case 'gesture_cooldown':
      return (
        <div className="pt-1" data-testid={`check-metrics-${check.check_type}`}>
          <DistributionBars distribuicao={m.ocorrencias_por_gesto} labelFor={(k) => k} />
        </div>
      );
    case 'descriptor_cooldown':
      return (
        <div className="pt-1" data-testid={`check-metrics-${check.check_type}`}>
          <DistributionBars distribuicao={m.ocorrencias_por_descritor} labelFor={(k) => k} />
        </div>
      );
    case 'prose_rhythm':
      return (
        <p className="text-xs text-[#6B7280]" data-testid={`check-metrics-${check.check_type}`}>
          {t('results.metrics_prose_rhythm', {
            media: fmt(m.media_palavras),
            desvio: fmt(m.desvio_padrao),
            min: m.minimo,
            max: m.maximo,
          })}
        </p>
      );
    case 'dialogue_tag_variety':
      return (
        <p className="text-xs text-[#6B7280]" data-testid={`check-metrics-${check.check_type}`}>
          {t('results.metrics_dialogue_tags', { withAdverb: m.falas_com_adverbio, total: m.falas_com_tag_detectadas })}
        </p>
      );
    case 'paragraph_opening_monotony':
      return (
        <p className="text-xs text-[#6B7280]" data-testid={`check-metrics-${check.check_type}`}>
          {t('results.metrics_paragraph_opening', { total: m.total_paragrafos, max: m.maior_repeticao, limite: m.limite })}
        </p>
      );
    default:
      return null;
  }
}

function CheckCard({ check, judgment = false }) {
  const { t } = useTranslation();
  const isVerified = check.confiabilidade === 'verificado';

  const copy = (text) => {
    navigator.clipboard.writeText(text);
    toast.success(t('results.copied'));
  };

  return (
    <div
      className={`rounded-xl border p-4 space-y-3 ${judgment ? 'border-amber-500/10 bg-[#161310]' : 'border-white/5 bg-[#121215]'}`}
      data-testid={`check-card-${check.check_type}`}
    >
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-[#F4F4F5] text-sm">{t(`checks.${check.check_type}`)}</h4>
        {judgment ? (
          <span className="flex items-center gap-1 text-xs text-amber-400" data-testid={`check-reliability-${check.check_type}`}>
            <Sparkles size={12} />
            {t('results.critical_tab')}
          </span>
        ) : (
          <span
            className={`flex items-center gap-1 text-xs ${isVerified ? 'text-emerald-400' : 'text-amber-400'}`}
            data-testid={`check-reliability-${check.check_type}`}
          >
            {isVerified ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
            {isVerified ? t('results.verified_badge') : t('results.generic_badge')}
          </span>
        )}
      </div>
      <p className="text-xs text-[#9CA3AF]">{t('results.occurrences', { count: check.contagem })}</p>
      {check.summary ? (
        <p className="text-xs text-[#9CA3AF] italic">{check.summary}</p>
      ) : (
        check.detalhes?.length === 0 && (
          <p className="text-xs text-[#9CA3AF] italic" data-testid={`check-no-issues-${check.check_type}`}>
            {judgment ? t('results.no_issues_judgment') : t('results.no_issues')}
          </p>
        )
      )}
      {check.check_type === 'sensory_rotation' && <SensoryDistribution distribuicao={check.distribuicao} />}
      {!judgment && <CheckMetrics check={check} />}
      <div className="space-y-2">
        {check.detalhes?.map((d, idx) => (
          <div
            key={idx}
            className={`rounded-lg p-3 space-y-2 border ${judgment ? 'bg-amber-500/10 border-amber-500/20' : 'bg-emerald-500/10 border-emerald-500/20'}`}
            data-testid={`check-detail-${check.check_type}-${idx}`}
          >
            <p className="text-sm text-[#E6E4DD]">
              <span className={judgment ? 'bg-amber-500/20 border-b border-amber-500/50' : 'bg-emerald-500/20 border-b border-emerald-500/50'}>
                {d.trecho}
              </span>
            </p>
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs text-[#9CA3AF]">{d.sugestao}</p>
              <Button
                size="icon"
                variant="ghost"
                data-testid={`copy-suggestion-${check.check_type}-${idx}`}
                onClick={() => copy(d.sugestao)}
                className="h-6 w-6 shrink-0 text-[#9CA3AF] hover:text-[#E6E4DD]"
                title={t('results.copy_suggestion')}
              >
                <Copy size={12} />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AnalysisResult({ analysis, analysisRunId, idSuffix = '' }) {
  const { t, i18n } = useTranslation();
  const [exporting, setExporting] = useState(null);
  if (!analysis) return null;

  const leituraCritica = analysis.leitura_critica || {};
  const judgmentChecks = leituraCritica.checks || [];
  const hasJudgmentResults = judgmentChecks.length > 0;

  const exportReport = async (format) => {
    const runId = analysisRunId || analysis.id || analysis.analysis_run_id;
    if (!runId) return;
    setExporting(format);
    try {
      const { data } = await api.get(`/analysis_runs/${runId}/export`, {
        params: { format, lang: i18n.language },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `cowriter-relatorio-${runId.slice(0, 8)}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error(t('results.export_error'));
    } finally {
      setExporting(null);
    }
  };

  return (
    <div data-testid={`analysis-result${idSuffix ? `-${idSuffix}` : ''}`} className="space-y-4">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4 text-xs text-[#9CA3AF]">
          <span data-testid="analysis-words-analyzed">{t('results.words_analyzed')}: {analysis.palavras_analisadas}</span>
          <span data-testid="analysis-credits-used">{t('results.credits_used')}: {analysis.creditos_consumidos}</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            data-testid="export-md-button"
            onClick={() => exportReport('md')}
            disabled={exporting !== null}
            className="h-7 text-xs gap-1.5 border-white/10 text-[#9CA3AF] hover:text-[#E6E4DD]"
          >
            <FileText size={12} /> {exporting === 'md' ? t('results.exporting') : t('results.export_md')}
          </Button>
          <Button
            size="sm"
            variant="outline"
            data-testid="export-pdf-button"
            onClick={() => exportReport('pdf')}
            disabled={exporting !== null}
            className="h-7 text-xs gap-1.5 border-white/10 text-[#9CA3AF] hover:text-[#E6E4DD]"
          >
            <Download size={12} /> {exporting === 'pdf' ? t('results.exporting') : t('results.export_pdf')}
          </Button>
        </div>
      </div>
      <Tabs defaultValue="fatos">
        <TabsList data-testid="analysis-tabs">
          <TabsTrigger value="fatos" data-testid="tab-fatos">{t('results.facts_tab')}</TabsTrigger>
          <TabsTrigger value="critica" data-testid="tab-critica">{t('results.critical_tab')}</TabsTrigger>
        </TabsList>
        <TabsContent value="fatos" className="space-y-3 mt-4">
          {analysis.fatos?.map((check) => (
            <CheckCard key={check.check_type} check={check} />
          ))}
        </TabsContent>
        <TabsContent value="critica" className="mt-4 space-y-3">
          <div className="bg-amber-500/10 text-amber-400 p-3 rounded border border-amber-500/20 text-xs" data-testid="critical-disclaimer">
            {t('results.disclaimer')}
          </div>
          {hasJudgmentResults ? (
            judgmentChecks.map((check) => (
              <CheckCard key={check.check_type} check={check} judgment />
            ))
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-[#9CA3AF]" data-testid="critical-coming-soon">
                {leituraCritica.status === 'sem_credito'
                  ? t('results.no_credit_message')
                  : t('results.coming_soon')}
              </p>
              {leituraCritica.status === 'sem_credito' && (
                <Link
                  to="/comprar-creditos"
                  data-testid="results-buy-credits-link"
                  className="inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 border border-emerald-400/30 px-4 py-1.5 text-xs text-emerald-400 hover:bg-emerald-400/20 transition-colors duration-200"
                >
                  {t('payments.buy_credits')}
                </Link>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
