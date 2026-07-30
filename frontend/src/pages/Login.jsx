import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { Feather } from 'lucide-react';
import { supabase } from '../lib/supabaseClient';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from '../components/ui/sonner';

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      toast.error(t('auth.error_invalid'));
      return;
    }
    navigate('/dashboard');
  };

  const handleGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-[#0C0C0E] px-4"
      style={{
        backgroundImage:
          'linear-gradient(rgba(12,12,14,0.85), rgba(12,12,14,0.95)), url(https://images.unsplash.com/photo-1578662996442-48f60103fc96?crop=entropy&cs=srgb&fm=jpg&q=85)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      <div className="w-full max-w-sm rounded-2xl border border-white/10 bg-[#121215]/90 p-8 space-y-6">
        <div className="flex items-center gap-2 justify-center">
          <Feather size={22} strokeWidth={1.5} className="text-emerald-400" />
          <span className="font-semibold text-xl tracking-tight text-[#F4F4F5]">{t('app.name')}</span>
        </div>
        <h1 className="text-2xl font-semibold text-center text-[#F4F4F5] tracking-tight" data-testid="login-title">
          {t('auth.login_title')}
        </h1>
        <form onSubmit={handleLogin} className="space-y-3">
          <Input
            data-testid="login-email-input"
            type="email"
            placeholder={t('auth.email')}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="bg-[#0C0C0E] border-white/10 text-[#E6E4DD]"
          />
          <Input
            data-testid="login-password-input"
            type="password"
            placeholder={t('auth.password')}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="bg-[#0C0C0E] border-white/10 text-[#E6E4DD]"
          />
          <Button data-testid="login-submit-button" type="submit" disabled={loading} className="w-full bg-white text-black hover:bg-white/90">
            {t('auth.login_button')}
          </Button>
        </form>
        <Button
          data-testid="login-google-button"
          variant="outline"
          onClick={handleGoogle}
          className="w-full border-white/15 text-[#E6E4DD] hover:bg-white/5"
        >
          {t('auth.google_button')}
        </Button>
        <p className="text-center text-sm text-[#9CA3AF]">
          {t('auth.no_account')}{' '}
          <Link to="/signup" data-testid="login-signup-link" className="text-emerald-400 hover:underline">
            {t('auth.signup_link')}
          </Link>
        </p>
      </div>
    </div>
  );
}
