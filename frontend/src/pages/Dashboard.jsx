import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Plus, BookOpen, Trash2 } from 'lucide-react';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from '../components/ui/sonner';
import { SUPPORTED_LANGUAGES } from '../i18n';

export default function Dashboard() {
  const { t } = useTranslation();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [nome, setNome] = useState('');
  const [idioma, setIdioma] = useState('pt-BR');
  const [genero, setGenero] = useState('');
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/projects');
      setProjects(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post('/projects', { nome, idioma, genero: genero || null });
      setOpen(false);
      setNome('');
      setGenero('');
      load();
    } catch {
      toast.error('Erro ao criar projeto.');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    await api.delete(`/projects/${id}`);
    load();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10" data-testid="dashboard-page">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-[#F4F4F5]">{t('dashboard.title')}</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="dashboard-new-project-button" className="bg-white text-black hover:bg-white/90 rounded-full">
              <Plus size={16} className="mr-1" /> {t('dashboard.new_project')}
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#121215] border-white/10 text-[#E6E4DD]">
            <DialogHeader>
              <DialogTitle className="text-[#F4F4F5]">{t('dashboard.new_project')}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3">
              <Input
                data-testid="new-project-name-input"
                placeholder={t('dashboard.project_name')}
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
                className="bg-[#0C0C0E] border-white/10"
              />
              <Select value={idioma} onValueChange={setIdioma}>
                <SelectTrigger data-testid="new-project-language-select" className="bg-[#0C0C0E] border-white/10">
                  <SelectValue placeholder={t('dashboard.language')} />
                </SelectTrigger>
                <SelectContent className="bg-[#121215] border-white/10 text-[#E6E4DD]">
                  {SUPPORTED_LANGUAGES.map((l) => (
                    <SelectItem key={l.code} value={l.code}>{l.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                data-testid="new-project-genre-input"
                placeholder={t('dashboard.genre')}
                value={genero}
                onChange={(e) => setGenero(e.target.value)}
                className="bg-[#0C0C0E] border-white/10"
              />
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={() => setOpen(false)}>{t('dashboard.cancel')}</Button>
                <Button type="submit" data-testid="new-project-submit-button" disabled={creating} className="bg-white text-black hover:bg-white/90">
                  {t('dashboard.create')}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {!loading && projects.length === 0 && (
        <p className="text-[#9CA3AF]" data-testid="dashboard-empty-state">{t('dashboard.empty')}</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="projects-grid">
        {projects.map((p) => (
          <div
            key={p.id}
            data-testid={`project-card-${p.id}`}
            className="rounded-xl border border-white/5 bg-[#121215] p-5 space-y-3 hover:border-white/15 transition-colors duration-200"
          >
            <div className="flex items-center justify-between">
              <BookOpen size={18} strokeWidth={1.5} className="text-emerald-400" />
              <button
                data-testid={`project-delete-${p.id}`}
                onClick={() => handleDelete(p.id)}
                className="text-[#9CA3AF] hover:text-red-400 transition-colors duration-200"
                title={t('dashboard.delete')}
              >
                <Trash2 size={14} />
              </button>
            </div>
            <h3 className="font-medium text-[#F4F4F5]">{p.nome}</h3>
            <p className="text-xs text-[#9CA3AF]">{p.idioma} {p.genero ? `· ${p.genero}` : ''}</p>
            <Link to={`/projects/${p.id}`} data-testid={`project-open-${p.id}`}>
              <Button variant="outline" size="sm" className="w-full border-white/15 text-[#E6E4DD] hover:bg-white/5">
                {t('dashboard.open')}
              </Button>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
