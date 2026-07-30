import { useTranslation } from 'react-i18next';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';

export function AnalysisConfirmModal({ open, onOpenChange, estimate, onConfirm, loading }) {
  const { t } = useTranslation();
  if (!estimate) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="analysis-confirm-modal" className="bg-[#121215] border-white/10 text-[#E6E4DD]">
        <DialogHeader>
          <DialogTitle className="text-[#F4F4F5]">{t('modal.confirm_title')}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          <p className="text-base" data-testid="analysis-word-count">
            {t('modal.confirm_body', { words: estimate.palavras })}
          </p>
          <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-emerald-400 text-xs">
            {t('modal.cost_facts')}
          </div>
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-amber-400 text-xs" data-testid="analysis-cost-estimate">
            {t('modal.cost_ai', { credits: estimate.creditos_estimados_ia, balance: estimate.saldo_atual })}
          </div>
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
