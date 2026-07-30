import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Feather, Wallet, History, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useWallet } from '../contexts/WalletContext';
import { LanguageSelector } from './LanguageSelector';
import { Button } from './ui/button';

export function Header() {
  const { t } = useTranslation();
  const { user, signOut } = useAuth();
  const { saldo } = useWallet();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <header
      data-testid="global-header"
      className="sticky top-0 z-40 backdrop-blur-xl bg-[#0C0C0E]/80 border-b border-white/5"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        <Link to="/dashboard" className="flex items-center gap-2 shrink-0" data-testid="header-logo-link">
          <Feather size={20} strokeWidth={1.5} className="text-[#34D399]" />
          <span className="font-semibold tracking-tight text-[#F4F4F5]">{t('app.name')}</span>
        </Link>

        <div className="flex items-center gap-2 sm:gap-4">
          {user && (
            <>
              <Link
                to="/credits"
                data-testid="header-credit-counter"
                className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 font-mono text-sm tracking-tight text-white hover:bg-white/10 transition-colors duration-200"
                title={t('wallet.balance')}
              >
                <Wallet size={14} strokeWidth={1.5} />
                {saldo}
                <span className="hidden sm:inline text-[#9CA3AF]">{t('wallet.credits')}</span>
              </Link>
              <Link
                to="/credits"
                data-testid="header-history-link"
                className="hidden sm:flex items-center gap-1.5 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] transition-colors duration-200"
              >
                <History size={16} strokeWidth={1.5} />
                {t('nav.history')}
              </Link>
            </>
          )}
          <LanguageSelector />
          {user && (
            <Button
              data-testid="header-logout-button"
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-[#9CA3AF] hover:text-[#E6E4DD]"
            >
              <LogOut size={16} strokeWidth={1.5} />
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
