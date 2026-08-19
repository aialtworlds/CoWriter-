import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import ptBR from './locales/pt-BR.json';

export const SUPPORTED_LANGUAGES = [
  { code: 'pt-BR', label: 'Português (Brasil)' },
    { code: 'en', label: 'English' },
    ];
    
    i18n
      .use(LanguageDetector)
        .use(initReactI18next)
          .init({
              resources: {
                    en: { translation: en },
                          'pt-BR': { translation: ptBR },
                                pt: { translation: ptBR },
                                    },
                                        fallbackLng: 'pt-BR',
                                            interpolation: { escapeValue: false },
                                                detection: { order: ['localStorage', 'navigator'], caches: ['localStorage'] },
                                                  });
                                                  
                                                  export default i18n;import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@/index.css";
import "@/i18n";
import App from "@/App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}
