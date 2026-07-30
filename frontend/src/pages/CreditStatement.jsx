import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { useWallet } from '../contexts/WalletContext';

export default function CreditStatement() {
  const { t } = useTranslation();
  const { saldo } = useWallet();
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    api.get('/wallet/transactions').then(({ data }) => setTransactions(data));
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10" data-testid="credit-statement-page">
      <Link to="/dashboard" className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200" data-testid="back-to-dashboard-link">
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-[#F4F4F5]">{t('wallet.statement_title')}</h1>
        <span className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 font-mono text-sm text-white" data-testid="statement-balance">
          {saldo} {t('wallet.credits')}
        </span>
      </div>

      {transactions.length === 0 && (
        <p className="text-[#9CA3AF]" data-testid="statement-empty">{t('wallet.empty')}</p>
      )}

      <div className="space-y-2" data-testid="transactions-list">
        {transactions.map((tx) => (
          <div
            key={tx.id}
            data-testid={`transaction-item-${tx.id}`}
            className="flex items-center justify-between rounded-lg border border-white/5 bg-[#121215] p-3 text-sm"
          >
            <div>
              <p className="text-[#F4F4F5]">{t(`wallet.${tx.tipo}`)}</p>
              <p className="text-xs text-[#9CA3AF]">{new Date(tx.criado_em).toLocaleString()}</p>
            </div>
            <span className={Number(tx.quantidade) >= 0 ? 'text-emerald-400 font-mono' : 'text-amber-400 font-mono'}>
              {Number(tx.quantidade) >= 0 ? '+' : ''}{tx.quantidade}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
