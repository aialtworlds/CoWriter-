import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from './ui/select';

const EXPLANATION_LANGUAGES = [
  { value: 'pt-BR', label: 'Português (Brasil)' },
  { value: 'en', label: 'English' },
];

export function AnalysisConfirmModal({
  open,
  onOpenChange,
  estimate,
  onConfirm,
  loading,
  includeCritical,
  onIncludeCriticalChange,
  explanationLanguage,
  onExplanationLanguageChange,
}) {
  const { t } = useTranslation();
  if (!estimate) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="analysis-confirm-modal" className="bg-[#121215] border-white/10 text-[#E6E4DD]">
        <DialogHeader>
          <DialogTitle className="text-[#F4F4F5]">{t('modal.confirm_title')}</DialogTitle>
          <DialogDescription className="text-[#9CA3AF]">
            {t('modal.confirm_body', { words: estimate.palavras })}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          <p className="text-base" data-testid="analysis-word-count">
            {t('modal.confirm_body', { words: estimate.palavras })}
          </p>
          <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-emerald-400 text-xs">
            {t('modal.cost_facts')}
          </div>
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-amber-400 text-xs" data-testid="analysis-cost-estimate">
            <label className="flex items-start gap-2 cursor-pointer">
              <Checkbox
                checked={includeCritical}
                onCheckedChange={onIncludeCriticalChange}
                data-testid="include-critical-reading-checkbox"
                className="mt-0.5 border-amber-400/40 data-[state=checked]:bg-amber-400 data-[state=checked]:border-amber-400"
              />
              <span>{t('modal.cost_ai', { credits: estimate.creditos_estimados_ia, balance: estimate.saldo_atual })}</span>
            </label>
          </div>

          {includeCritical && (
            <div className="space-y-1.5" data-testid="explanation-language-row">
              <label className="text-xs text-[#9CA3AF]">{t('modal.explanation_lang_label')}</label>
              <Select value={explanationLanguage || '__same__'} onValueChange={(v) => onExplanationLanguageChange(v === '__same__' ? '' : v)}>
                <SelectTrigger data-testid="explanation-language-select" className="bg-[#0C0C0E] border-white/10 text-[#E6E4DD] h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#121215] border-white/10 text-[#E6E4DD]">
                  <SelectItem value="__same__">{t('modal.explanation_lang_same')}</SelectItem>
                  {EXPLANATION_LANGUAGES.map((l) => (
                    <SelectItem key={l.value} value={l.value}>{l.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-[11px] text-[#9CA3AF]">{t('modal.explanation_lang_hint')}</p>
            </div>
          )}

          {includeCritical && !estimate.saldo_suficiente && estimate.creditos_estimados_ia > 0 && (
            <Link
              to="/comprar-creditos"
              data-testid="modal-buy-credits-link"
              className="inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 border border-emerald-400/30 px-4 py-1.5 text-xs text-emerald-400 hover:bg-emerald-400/20 transition-colors duration-200"
            >
              {t('payments.buy_credits')}
            </Link>
          )}
        </div>
        <DialogFooter>
          <Button variant="ghost" data-testid="analysis-cancel-button" onClick={() => onOpenChange(false)}>
            {t('modal.cancel_button')}
          </Button>
          <Button
            data-testid="analysis-confirm-button"
            onClick={onConfirm}
            disabled={loading}
            className="bg-white text-black hover:bg-white/90"
          >
            {loading ? t('chapter.analyzing') : t('modal.confirm_button')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
