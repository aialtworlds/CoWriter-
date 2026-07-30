import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Plus, Trash2, Download, Upload } from 'lucide-react';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from '../components/ui/sonner';

const TIPOS = ['frase', 'gesto', 'descritor', 'estrutura'];

export default function RulesPage() {
  const { projectId } = useParams();
  const { t } = useTranslation();
  const [scope, setScope] = useState('project');
  const [rules, setRules] = useState([]);
  const [tipo, setTipo] = useState('frase');
  const [texto, setTexto] = useState('');
  const [cooldownMax, setCooldownMax] = useState(1);
  const [importTipo, setImportTipo] = useState('frase');
  const [importTexto, setImportTexto] = useState('');
  const [loading, setLoading] = useState(false);

  const scopeProjectId = scope === 'project' ? projectId : undefined;

  const load = async () => {
    const { data } = await api.get('/banned_patterns', { params: scopeProjectId ? { project_id: scopeProjectId } : {} });
    setRules(data);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!texto.trim()) return;
    setLoading(true);
    try {
      await api.post('/banned_patterns', {
        tipo,
        texto_padrao: texto,
        cooldown_max: Number(cooldownMax) || 1,
        project_id: scope === 'project' ? projectId : null,
      });
      setTexto('');
      load();
    } catch {
      toast.error('Erro ao criar regra.');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!importTexto.trim()) return;
    setLoading(true);
    try {
      const { data } = await api.post('/banned_patterns/import', {
        tipo: importTipo,
        texto: importTexto,
        project_id: scope === 'project' ? projectId : null,
      });
      toast.success(`${data.length} regra(s) importada(s).`);
      setImportTexto('');
      load();
    } catch {
      toast.error('Erro ao importar regras.');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    const params = scopeProjectId ? { project_id: scopeProjectId } : {};
    const { data } = await api.get('/banned_patterns/export', { params, responseType: 'blob' });
    const url = URL.createObjectURL(new Blob([data], { type: 'text/plain' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `cowriter-regras-${scope}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = async (id) => {
    await api.delete(`/banned_patterns/${id}`);
    load();
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10" data-testid="rules-page">
      <Link
        to={projectId ? `/projects/${projectId}` : '/dashboard'}
        className="flex items-center gap-1 text-sm text-[#9CA3AF] hover:text-[#E6E4DD] mb-6 transition-colors duration-200"
        data-testid="back-from-rules-link"
      >
        <ArrowLeft size={14} /> {t('project.back_to_projects')}
      </Link>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-[#F4F4F5]">{t('rules.title')}</h1>
        <Button
          variant="outline"
          data-testid="export-rules-button"
          onClick={handleExport}
          className="border-white/15 text-[#E6E4DD] hover:bg-white/5"
        >
          <Download size={14} className="mr-1" /> {t('rules.export_button')}
        </Button>
      </div>

      {projectId && (
        <Tabs value={scope} onValueChange={setScope} className="mb-6">
          <TabsList data-testid="rules-scope-tabs">
            <TabsTrigger value="project" data-testid="rules-scope-project">{t('rules.scope_project')}</TabsTrigger>
            <TabsTrigger value="global" data-testid="rules-scope-global">{t('rules.scope_global')}</TabsTrigger>
          </TabsList>
        </Tabs>
      )}

      <form onSubmit={handleCreate} className="rounded-xl border border-white/5 bg-[#121215] p-4 mb-6 space-y-3">
        <h3 className="text-sm font-medium text-[#F4F4F5]">{t('rules.new_rule')}</h3>
        <div className="flex flex-wrap gap-3">
          <Select value={tipo} onValueChange={setTipo}>
            <SelectTrigger data-testid="new-rule-type-select" className="w-48 bg-[#0C0C0E] border-white/10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#121215] border-white/10 text-[#E6E4DD]">
              {TIPOS.map((tp) => (
                <SelectItem key={tp} value={tp}>{t(`rules.type_${tp}`)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            data-testid="new-rule-text-input"
            placeholder={t('rules.text_placeholder')}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            className="flex-1 min-w-[200px] bg-[#0C0C0E] border-white/10"
          />
          {(tipo === 'gesto' || tipo === 'descritor') && (
            <Input
              data-testid="new-rule-cooldown-input"
              type="number"
              min={1}
              value={cooldownMax}
              onChange={(e) => setCooldownMax(e.target.value)}
              className="w-40 bg-[#0C0C0E] border-white/10"
              title={t('rules.cooldown_label')}
            />
          )}
          <Button type="submit" data-testid="new-rule-submit-button" disabled={loading} className="bg-white text-black hover:bg-white/90">
            <Plus size={14} className="mr-1" /> {t('rules.add_button')}
          </Button>
        </div>
      </form>

      <div className="rounded-xl border border-white/5 bg-[#121215] p-4 mb-8 space-y-3">
        <h3 className="text-sm font-medium text-[#F4F4F5]">{t('rules.import_title')}</h3>
        <div className="flex flex-wrap gap-3 items-start">
          <Select value={importTipo} onValueChange={setImportTipo}>
            <SelectTrigger data-testid="import-rule-type-select" className="w-48 bg-[#0C0C0E] border-white/10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#121215] border-white/10 text-[#E6E4DD]">
              {TIPOS.map((tp) => (
                <SelectItem key={tp} value={tp}>{t(`rules.type_${tp}`)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Textarea
            data-testid="import-rules-textarea"
            placeholder={t('rules.import_placeholder')}
            value={importTexto}
            onChange={(e) => setImportTexto(e.target.value)}
            className="flex-1 min-w-[200px] min-h-[80px] bg-[#0C0C0E] border-white/10"
          />
          <Button
            type="button"
            data-testid="import-rules-button"
            onClick={handleImport}
            disabled={loading}
            variant="outline"
            className="border-white/15 text-[#E6E4DD] hover:bg-white/5"
          >
            <Upload size={14} className="mr-1" /> {t('rules.import_button')}
          </Button>
        </div>
      </div>

      {rules.length === 0 && (
        <p className="text-[#9CA3AF]" data-testid="rules-empty-state">{t('rules.empty')}</p>
      )}

      <div className="space-y-2" data-testid="rules-list">
        {rules.map((r) => (
          <div
            key={r.id}
            data-testid={`rule-item-${r.id}`}
            className="flex items-center justify-between rounded-lg border border-white/5 bg-[#121215] p-3"
          >
            <div>
              <span className="text-xs text-emerald-400 mr-2 uppercase tracking-wide">{t(`rules.type_${r.tipo}`)}</span>
              <span className="text-[#E6E4DD]">{r.texto_padrao}</span>
              {!r.project_id && scope === 'global' && (
                <span className="ml-2 text-xs text-[#9CA3AF]">({t('rules.scope_global')})</span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-amber-400" data-testid={`rule-disparos-${r.id}`}>
                {t('rules.triggered', { count: r.disparos_count })}
              </span>
              <button
                data-testid={`delete-rule-${r.id}`}
                onClick={() => handleDelete(r.id)}
                className="text-[#9CA3AF] hover:text-red-400 transition-colors duration-200"
                title={t('rules.delete')}
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
