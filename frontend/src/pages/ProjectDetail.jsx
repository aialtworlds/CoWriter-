import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Plus, FileText, Coins, ListChecks } from 'lucide-react';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';

export default function ProjectDetail() {
  const { projectId } = useParams();
  const { t } = useTranslation();
  const [project, setProject] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    api.get(`/projects/${projectId}`).then(({ data }) => setProject(data));
    api.get(`/projects/${projectId}/history`).then(({ data }) => setHistory(data));
  }, [projectId]);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10" data-testid="project-detail-page">
      <Link to="/dashboard" className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200" data-testid="back-to-dashboard-link">
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-[#F4F4F5]" data-testid="project-detail-name">
            {project?.nome}
          </h1>
          <p className="text-sm text-[#9CA3AF]">{project?.idioma} {project?.genero ? `· ${project.genero}` : ''}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/projects/${projectId}/rules`}>
            <Button variant="outline" data-testid="project-rules-link" className="border-white/15 text-[#E6E4DD] hover:bg-white/5">
              <ListChecks size={14} className="mr-1" /> {t('rules.title')}
            </Button>
          </Link>
          <Link to="/credits">
            <Button variant="outline" data-testid="project-credit-statement-link" className="border-white/15 text-[#E6E4DD] hover:bg-white/5">
              <Coins size={14} className="mr-1" /> {t('project.credit_statement')}
            </Button>
          </Link>
          <Link to={`/projects/${projectId}/chapters/new`}>
            <Button data-testid="project-new-chapter-button" className="bg-white text-black hover:bg-white/90 rounded-full">
              <Plus size={16} className="mr-1" /> {t('project.new_chapter')}
            </Button>
          </Link>
        </div>
      </div>

      <h2 className="text-lg font-medium text-[#F4F4F5] mb-4">{t('project.chapters')}</h2>

      {history.length === 0 && (
        <p className="text-[#9CA3AF]" data-testid="project-empty-chapters">{t('project.empty_chapters')}</p>
      )}

      <div className="space-y-3" data-testid="chapters-history-list">
        {history.map((h) => (
          <div
            key={h.chapter_id}
            data-testid={`chapter-history-item-${h.chapter_id}`}
            className="rounded-xl border border-white/5 bg-[#121215] p-4 flex items-center justify-between hover:border-white/15 transition-colors duration-200"
          >
            <div className="flex items-center gap-3">
              <FileText size={18} strokeWidth={1.5} className="text-emerald-400" />
              <div>
                <p className="font-medium text-[#F4F4F5]">{h.titulo}</p>
                {h.analysis_run_id && (
                  <p className="text-xs text-[#9CA3AF]">
                    {h.palavras_analisadas} palavras · {new Date(h.timestamp).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
            {h.analysis_run_id ? (
              <Link to={`/analysis/${h.analysis_run_id}`} data-testid={`chapter-view-result-${h.chapter_id}`}>
                <Button variant="outline" size="sm" className="border-white/15 text-[#E6E4DD] hover:bg-white/5">
                  Ver análise
                </Button>
              </Link>
            ) : (
              <Link to={`/chapters/${h.chapter_id}`} data-testid={`chapter-analyze-${h.chapter_id}`}>
                <Button variant="outline" size="sm" className="border-white/15 text-[#E6E4DD] hover:bg-white/5">
                  {t('chapter.analyze')}
                </Button>
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
