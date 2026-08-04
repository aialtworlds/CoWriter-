import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { XCircle } from 'lucide-react';
import { Button } from '../components/ui/button';

export default function PaymentCancel() {
  const { t } = useTranslation();

  return (
    <div className="max-w-md mx-auto px-4 sm:px-6 py-24 text-center" data-testid="payment-cancel-page">
      <XCircle size={40} className="text-amber-400 mx-auto mb-4" />
      <h1 className="text-2xl font-semibold text-[#F4F4F5] mb-2" data-testid="payment-cancel-title">
        {t('payments.cancel_title')}
      </h1>
      <p className="text-[#9CA3AF] mb-8" data-testid="payment-cancel-message">
        {t('payments.cancel_message')}
      </p>
      <Link to="/comprar-creditos">
        <Button data-testid="payment-cancel-retry-button" className="bg-white text-black hover:bg-white/90 rounded-full">
          {t('payments.try_again')}
        </Button>
      </Link>
    </div>
  );
}
