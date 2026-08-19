import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Plus, FileText, Coins, ListChecks, Pencil, Trash2, Check, X } from 'lucide-react';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from '../components/ui/sonner';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from '../components/ui/alert-dialog';

export default function ProjectDetail() {
  const { projectId } = useParams();
  const { t } = useTranslation();
  const [project, setProject] = useState(null);
  const [history, setHistory] = useState([]);

  const [editingProjectName, setEditingProjectName] = useState(false);
  const [projectNameDraft, setProjectNameDraft] = useState('');

  const [editingChapterId, setEditingChapterId] = useState(null);
  const [chapterTitleDraft, setChapterTitleDraft] = useState('');

  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadProject = () => api.get(`/projects/${projectId}`).then(({ data }) => setProject(data));
  const loadHistory = () => api.get(`/projects/${projectId}/history`).then(({ data }) => setHistory(data));

  useEffect(() => {
    loadProject();
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const startEditProjectName = () => {
    setProjectNameDraft(project?.nome || '');
    setEditingProjectName(true);
  };

  const saveProjectName = async () => {
    if (!projectNameDraft.trim()) return;
    try {
      const { data } = await api.put(`/projects/${projectId}`, { nome: projectNameDraft.trim() });
      setProject(data);
      setEditingProjectName(false);
    } catch {
      toast.error('Erro ao salvar nome do projeto.');
    }
  };

  const startEditChapterTitle = (chapter) => {
    setEditingChapterId(chapter.chapter_id);
    setChapterTitleDraft(chapter.titulo);
  };

  const saveChapterTitle = async (chapterId) => {
    if (!chapterTitleDraft.trim()) return;
    try {
      await api.patch(`/chapters/${chapterId}`, { titulo: chapterTitleDraft.trim() });
      setEditingChapterId(null);
      await loadHistory();
    } catch {
      toast.error('Erro ao salvar título do capítulo.');
    }
  };

  const confirmDeleteChapter = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/chapters/${deleteTarget.chapter_id}`);
      setDeleteTarget(null);
      await loadHistory();
    } catch {
      toast.error('Erro ao excluir capítulo.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10" data-testid="project-detail-page">
      <Link to="/dashboard" className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200" data-testid="back-to-dashboard-link">
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>

      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div className="flex-1 min-w-0">
          {editingProjectName ? (
            <div className="flex items-center gap-2" data-testid="project-name-edit-row">
              <Input
                autoFocus
                value={projectNameDraft}
                onChange={(e) => setProjectNameDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') saveProjectName();
                  if (e.key === 'Escape') setEditingProjectName(false);
                }}
                className="bg-[#121215] border-white/10 text-[#E6E4DD] text-2xl h-auto py-1"
                data-testid="project-name-input"
              />
              <Button size="icon" variant="ghost" onClick={saveProjectName} data-testid="project-name-save-button" className="text-emerald-400 hover:text-emerald-300 shrink-0">
                <Check size={18} />
              </Button>
              <Button size="icon" variant="ghost" onClick={() => setEditingProjectName(false)} data-testid="project-name-cancel-button" className="text-[#9CA3AF] hover:text-[#E6E4DD] shrink-0">
                <X size={18} />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 group">
              <h1 className="text-3xl font-semibold tracking-tight text-[#F4F4F5]" data-testid="project-detail-name">
                {project?.nome}
              </h1>
              <button
                onClick={startEditProjectName}
                data-testid="project-name-edit-button"
                aria-label={t('common.edit')}
                className="text-[#9CA3AF] hover:text-[#E6E4DD] opacity-0 group-hover:opacity-100 transition-opacity duration-200 shrink-0"
              >
                <Pencil size={16} />
              </button>
            </div>
          )}
          <p className="text-sm text-[#9CA3AF] mt-1">{project?.idioma} {project?.genero ? `· ${project.genero}` : ''}</p>
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
            className="rounded-xl border border-white/5 bg-[#121215] p-4 flex items-center justify-between gap-3 hover:border-white/15 transition-colors duration-200 group"
          >
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <FileText size={18} strokeWidth={1.5} className="text-emerald-400 shrink-0" />
              <div className="min-w-0 flex-1">
                {editingChapterId === h.chapter_id ? (
                  <div className="flex items-center gap-2">
                    <Input
                      autoFocus
                      value={chapterTitleDraft}
                      onChange={(e) => setChapterTitleDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveChapterTitle(h.chapter_id);
                        if (e.key === 'Escape') setEditingChapterId(null);
                      }}
                      className="bg-[#0C0C0E] border-white/10 text-[#E6E4DD] h-8"
                      data-testid={`chapter-title-input-${h.chapter_id}`}
                    />
                    <Button size="icon" variant="ghost" onClick={() => saveChapterTitle(h.chapter_id)} data-testid={`chapter-title-save-${h.chapter_id}`} className="text-emerald-400 hover:text-emerald-300 h-8 w-8 shrink-0">
                      <Check size={16} />
                    </Button>
                    <Button size="icon" variant="ghost" onClick={() => setEditingChapterId(null)} data-testid={`chapter-title-cancel-${h.chapter_id}`} className="text-[#9CA3AF] hover:text-[#E6E4DD] h-8 w-8 shrink-0">
                      <X size={16} />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-[#F4F4F5] truncate">{h.titulo}</p>
                    <button
                      onClick={() => startEditChapterTitle(h)}
                      data-testid={`chapter-title-edit-${h.chapter_id}`}
                      aria-label={t('common.edit')}
                      className="text-[#9CA3AF] hover:text-[#E6E4DD] opacity-0 group-hover:opacity-100 transition-opacity duration-200 shrink-0"
                    >
                      <Pencil size={14} />
                    </button>
                  </div>
                )}
                {h.analysis_run_id && (
                  <p className="text-xs text-[#9CA3AF]">
                    {h.palavras_analisadas} palavras · {new Date(h.timestamp).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
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
              <Button
                size="icon"
                variant="ghost"
                onClick={() => setDeleteTarget(h)}
                data-testid={`chapter-delete-${h.chapter_id}`}
                aria-label={t('common.delete')}
                className="text-[#9CA3AF] hover:text-red-400 h-8 w-8"
              >
                <Trash2 size={16} />
              </Button>
            </div>
          </div>
        ))}
      </div>

      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent data-testid="chapter-delete-confirm-dialog" className="bg-[#121215] border-white/10 text-[#E6E4DD]">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-[#F4F4F5]">{t('chapter.delete_confirm_title')}</AlertDialogTitle>
            <AlertDialogDescription className="text-[#9CA3AF]">
              {t('chapter.delete_confirm_body')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="chapter-delete-cancel-button">{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteChapter}
              data-testid="chapter-delete-confirm-button"
              className="bg-red-500 text-white hover:bg-red-600"
            >
              {t('common.delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
