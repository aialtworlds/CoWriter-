import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { CheckCircle2, Loader2 } from 'lucide-react';
import { api } from '../lib/api';
import { useWallet } from '../contexts/WalletContext';
import { Button } from '../components/ui/button';

const MAX_POLLS = 15;
const POLL_INTERVAL_MS = 2000;

export default function PaymentSuccess() {
  const { t } = useTranslation();
  const { refresh } = useWallet();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [status, setStatus] = useState('confirming');
  const [creditos, setCreditos] = useState(null);
  const pollCount = useRef(0);

  useEffect(() => {
    if (!sessionId) {
      setStatus('error');
      return;
    }
    let timer;
    const poll = async () => {
      try {
        const { data } = await api.get(`/payments/status/${sessionId}`);
        if (data.status === 'paid') {
          setCreditos(data.creditos_concedidos);
          setStatus('paid');
          refresh();
          return;
        }
      } catch {
        // keep polling until MAX_POLLS
      }
      pollCount.current += 1;
      if (pollCount.current < MAX_POLLS) {
        timer = setTimeout(poll, POLL_INTERVAL_MS);
      } else {
        setStatus('timeout');
      }
    };
    poll();
    return () => clearTimeout(timer);
  }, [sessionId, refresh]);

  return (
    <div className="max-w-md mx-auto px-4 sm:px-6 py-24 text-center" data-testid="payment-success-page">
      {status === 'confirming' && (
        <>
          <Loader2 size={32} className="animate-spin text-emerald-400 mx-auto mb-4" />
          <p className="text-[#E6E4DD]" data-testid="payment-confirming-message">{t('payments.confirming')}</p>
        </>
      )}
      {status === 'timeout' && (
        <>
          <Loader2 size={32} className="text-amber-400 mx-auto mb-4" />
          <p className="text-[#E6E4DD]" data-testid="payment-timeout-message">{t('payments.confirming_timeout')}</p>
        </>
      )}
      {status === 'paid' && (
        <>
          <CheckCircle2 size={40} className="text-emerald-400 mx-auto mb-4" />
          <h1 className="text-2xl font-semibold text-[#F4F4F5] mb-2" data-testid="payment-success-title">
            {t('payments.success_title')}
          </h1>
          <p className="text-[#9CA3AF] mb-8" data-testid="payment-success-message">
            {t('payments.success_message', { credits: creditos })}
          </p>
          <Link to="/dashboard">
            <Button data-testid="payment-success-back-button" className="bg-white text-black hover:bg-white/90 rounded-full">
              {t('payments.back_to_dashboard')}
            </Button>
          </Link>
        </>
      )}
      {status === 'error' && (
        <p className="text-[#9CA3AF]" data-testid="payment-error-message">{t('payments.checkout_error')}</p>
      )}
    </div>
  );
}
