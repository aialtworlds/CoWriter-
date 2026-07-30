import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES } from '../i18n';

export function LanguageSelector({ className = '' }) {
  const { i18n } = useTranslation();

  return (
    <select
      data-testid="language-selector"
      value={i18n.language}
      onChange={(e) => i18n.changeLanguage(e.target.value)}
      className={`bg-transparent border border-white/10 rounded-full text-xs px-3 py-1.5 text-[#E6E4DD] focus:outline-none focus:ring-2 focus:ring-white/30 cursor-pointer ${className}`}
    >
      {SUPPORTED_LANGUAGES.map((lang) => (
        <option key={lang.code} value={lang.code} className="bg-[#121215]">
          {lang.label}
        </option>
      ))}
    </select>
  );
}
