import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Wallet, CreditCard, Sparkles } from 'lucide-react';
import { api } from '../lib/api';
import { useWallet } from '../contexts/WalletContext';
import { Button } from '../components/ui/button';
import { toast } from '../components/ui/sonner';

const PACKAGE_ICONS = {
  conto: Sparkles,
  romance_medio: CreditCard,
  romance_longo: Wallet,
};

export default function BuyCredits() {
  const { t } = useTranslation();
  const { saldo } = useWallet();
  const [packages, setPackages] = useState([]);
  const [buying, setBuying] = useState(null);

  useEffect(() => {
    api.get('/payments/packages').then(({ data }) => setPackages(data));
  }, []);

  const handleBuy = async (pacote) => {
    setBuying(pacote);
    try {
      const { data } = await api.post('/payments/checkout', {
        pacote,
        origin_url: window.location.origin,
      });
      window.location.href = data.checkout_url;
    } catch {
      toast.error(t('payments.checkout_error'));
      setBuying(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10" data-testid="buy-credits-page">
      <Link
        to="/dashboard"
        className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200"
        data-testid="back-to-dashboard-link"
      >
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>

      <div className="flex items-center justify-between mb-2 flex-wrap gap-4">
        <h1 className="text-3xl font-semibold tracking-tight text-[#F4F4F5]">{t('payments.page_title')}</h1>
        <span
          className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 font-mono text-sm text-white"
          data-testid="buy-credits-current-balance"
        >
          {t('payments.current_balance', { balance: saldo })}
        </span>
      </div>
      <p className="text-sm text-[#9CA3AF] mb-10">{t('payments.no_expiry_note')}</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6" data-testid="packages-grid">
        {packages.map((pkg) => {
          const Icon = PACKAGE_ICONS[pkg.pacote] || Wallet;
          return (
            <div
              key={pkg.pacote}
              data-testid={`package-card-${pkg.pacote}`}
              className="rounded-xl border border-white/5 bg-[#121215] p-6 flex flex-col gap-4 hover:border-emerald-400/30 transition-colors duration-200"
            >
              <Icon size={22} strokeWidth={1.5} className="text-emerald-400" />
              <div>
                <h3 className="font-medium text-[#F4F4F5]">{t(`payments.package_${pkg.pacote}`)}</h3>
                <p className="text-xs text-[#9CA3AF] mt-1">{t('payments.credits_label', { count: pkg.creditos })}</p>
              </div>
              <p className="text-2xl font-semibold text-[#F4F4F5] mt-auto" data-testid={`package-price-${pkg.pacote}`}>
                R$ {pkg.valor.toFixed(2).replace('.', ',')}
              </p>
              <Button
                data-testid={`package-buy-button-${pkg.pacote}`}
                onClick={() => handleBuy(pkg.pacote)}
                disabled={buying !== null}
                className="w-full bg-white text-black hover:bg-white/90 rounded-full"
              >
                {buying === pkg.pacote ? t('payments.redirecting') : t('payments.buy_button')}
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
