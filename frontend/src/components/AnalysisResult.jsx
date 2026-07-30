import { useTranslation } from 'react-i18next';
import { Copy, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { toast } from './ui/sonner';

function CheckCard({ check }) {
  const { t } = useTranslation();
  const isVerified = check.confiabilidade === 'verificado';

  const copy = (text) => {
    navigator.clipboard.writeText(text);
    toast.success(t('results.copied'));
  };

  return (
    <div className="rounded-xl border border-white/5 bg-[#121215] p-4 space-y-3" data-testid={`check-card-${check.check_type}`}>
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-[#F4F4F5] text-sm">{t(`checks.${check.check_type}`)}</h4>
        <span
          className={`flex items-center gap-1 text-xs ${isVerified ? 'text-emerald-400' : 'text-amber-400'}`}
          data-testid={`check-reliability-${check.check_type}`}
        >
          {isVerified ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
          {isVerified ? t('results.verified_badge') : t('results.generic_badge')}
        </span>
      </div>
      <p className="text-xs text-[#9CA3AF]">{t('results.occurrences', { count: check.contagem })}</p>
      {check.detalhes?.length === 0 && (
        <p className="text-xs text-[#9CA3AF] italic">{t('results.no_issues')}</p>
      )}
      <div className="space-y-2">
        {check.detalhes?.map((d, idx) => (
          <div key={idx} className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-3 space-y-2" data-testid={`check-detail-${check.check_type}-${idx}`}>
            <p className="text-sm text-[#E6E4DD]">
              <span className="bg-emerald-500/20 border-b border-emerald-500/50">{d.trecho}</span>
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

export function AnalysisResult({ analysis, idSuffix = '' }) {
  const { t } = useTranslation();
  if (!analysis) return null;

  return (
    <div data-testid={`analysis-result${idSuffix ? `-${idSuffix}` : ''}`} className="space-y-4">
      <div className="flex items-center gap-4 text-xs text-[#9CA3AF]">
        <span data-testid="analysis-words-analyzed">{t('results.words_analyzed')}: {analysis.palavras_analisadas}</span>
        <span data-testid="analysis-credits-used">{t('results.credits_used')}: {analysis.creditos_consumidos}</span>
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
          <p className="text-sm text-[#9CA3AF]" data-testid="critical-coming-soon">
            {t('results.coming_soon')}
          </p>
        </TabsContent>
      </Tabs>
    </div>
  );
}
