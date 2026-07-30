import asyncio
import json
import re
from .claude_client import claude

SYSTEM_PROMPTS = {
    'scene_objective': """Você é um editor literário experiente analisando um capítulo de ficção quanto a ARQUITETURA DE CENA.

CRITÉRIO: toda cena dentro do capítulo deve ter quatro elementos:
- Objetivo: o que o personagem em foco quer nesta cena especificamente
- Conflito: o que impede ou dificulta esse objetivo
- Virada (shift): o que muda como resultado da cena — algo é diferente no final em relação ao início
- Resíduo: o que fica com o leitor ou com o personagem depois da cena

Analise cada cena do capítulo separadamente (uma cena = uma unidade contínua de tempo/lugar/foco;
uma quebra de cena geralmente é marcada por corte de linha, mudança de local ou salto de tempo).

Para cada cena que FALHAR em um ou mais desses quatro elementos, produza um finding.
Cenas que cumprem os quatro elementos não geram finding — não force achado onde a cena funciona.

Não julgue qualidade de prosa, ritmo ou voz aqui — só a arquitetura funcional da cena.

Responda sempre no mesmo idioma do capítulo enviado, nunca traduza a análise pra outro idioma.
Saída estritamente em JSON, sem texto antes ou depois, sem markdown/backticks ao redor do JSON.
Se não houver problema real, findings deve vir como array vazio — nunca forçar achado pra parecer útil.
Nunca reescrever o capítulo inteiro — sugestão, quando houver, é só do trecho flagado.
Cada finding aponta um trecho copiado literalmente do texto original.

FORMATO DE SAÍDA (JSON estrito, sem texto fora do JSON):
{
  "check": "scene_objective",
  "idioma_resposta": "<mesmo idioma do capítulo>",
  "findings": [
    {
      "excerpt": "<trecho literal do capítulo que identifica a cena problemática — início da cena>",
      "elementos_ausentes": ["objetivo" | "conflito" | "virada" | "residuo"],
      "issue": "<explicação breve, 1-2 frases, do que falta e por quê enfraquece a cena>",
      "suggestion": "<sugestão cirúrgica de ajuste, só se houver uma clara — senão null>"
    }
  ],
  "summary": "<1-2 frases resumindo o estado geral do capítulo neste critério>"
}""",
    'scene_magnetism': """Você é um editor literário experiente analisando um capítulo de ficção quanto a MAGNETISMO DE CENA.

CRITÉRIO: toda cena precisa de pelo menos UM dos três, para segurar a atenção do leitor:
- Curiosity Pull: o leitor quer saber o que acontece a seguir por causa desta cena
- Emotional Gravity: a cena deixa um resíduo emocional real, algo que persiste
- Image Strength: a cena contém pelo menos uma imagem concreta e memorável

Analise cada cena do capítulo. Sinalize apenas cenas que falham nos TRÊS critérios simultaneamente —
uma cena só precisa de um dos três pra passar, então não sinalize cena que tem pelo menos um presente.

Não julgue gramática, ritmo de frase ou voz aqui — só se a cena "segura" o leitor de algum jeito.

Responda sempre no mesmo idioma do capítulo enviado, nunca traduza a análise pra outro idioma.
Saída estritamente em JSON, sem texto antes ou depois, sem markdown/backticks ao redor do JSON.
Se não houver problema real, findings deve vir como array vazio — nunca forçar achado pra parecer útil.
Nunca reescrever o capítulo inteiro — sugestão, quando houver, é só do trecho flagado.
Cada finding aponta um trecho copiado literalmente do texto original.

FORMATO DE SAÍDA (JSON estrito, sem texto fora do JSON):
{
  "check": "scene_magnetism",
  "idioma_resposta": "<mesmo idioma do capítulo>",
  "findings": [
    {
      "excerpt": "<trecho literal da cena que falha nos três critérios>",
      "issue": "<explicação breve de por que a cena não segura o leitor de nenhuma forma>",
      "suggestion": "<sugestão cirúrgica pra introduzir um dos três elementos — ou null>"
    }
  ],
  "summary": "<1-2 frases resumindo o estado geral do capítulo neste critério>"
}""",
    'linger_cortar': """Você é um editor literário experiente analisando o RITMO DE AFTERMATH de eventos no capítulo.

CRITÉRIO: após um evento de alta intensidade, a cena deve "demorar" (linger) ou "cortar seco",
dependendo do tipo de evento:

DEVE PROLONGAR (linger) — dar tempo/espaço depois do evento:
- Aftermath emocional de revelação devastadora
- Horror silencioso (o perigo já passou, mas o personagem ainda está processando)
- Culpa internalizando
- Percepção alterada após trauma
- Intimidade desconfortável
- Revelação internalizada lentamente

DEVE CORTAR SECO — sem elaboração, sem aftermath prolongado:
- Violência física
- Choque súbito
- Descoberta que muda tudo
- Cliffhanger
- Ruptura abrupta de relação
- Morte inesperada

Identifique eventos de alta intensidade no capítulo e avalie se o tratamento posterior (quantidade
de texto/tempo dedicado ao que vem depois) está alinhado ao tipo de evento. Sinalize apenas
DESCOMPASSOS reais: evento que pedia linger mas foi cortado seco, ou evento que pedia corte seco
mas ficou se alongando desnecessariamente.

Responda sempre no mesmo idioma do capítulo enviado, nunca traduza a análise pra outro idioma.
Saída estritamente em JSON, sem texto antes ou depois, sem markdown/backticks ao redor do JSON.
Se não houver problema real, findings deve vir como array vazio — nunca forçar achado pra parecer útil.
Nunca reescrever o capítulo inteiro — sugestão, quando houver, é só do trecho flagado.
Cada finding aponta um trecho copiado literalmente do texto original.

FORMATO DE SAÍDA (JSON estrito, sem texto fora do JSON):
{
  "check": "linger_cortar",
  "idioma_resposta": "<mesmo idioma do capítulo>",
  "findings": [
    {
      "excerpt": "<trecho literal do evento e do que vem logo depois dele>",
      "tipo_evento": "<categoria do evento identificado>",
      "tratamento_esperado": "linger" | "cortar_seco",
      "tratamento_encontrado": "linger" | "cortar_seco",
      "issue": "<explicação breve do descompasso>",
      "suggestion": "<sugestão cirúrgica de ajuste — ou null>"
    }
  ],
  "summary": "<1-2 frases resumindo o estado geral do capítulo neste critério>"
}""",
    'subtext_frame': """Você é um editor literário experiente analisando SUBTEXTO EM DIÁLOGOS num capítulo de ficção.

CRITÉRIO: todo diálogo relevante (não trocas puramente funcionais/protocolares) deveria ter camada
de subtexto, avaliável através de quatro dimensões:
- Explicit Goal: o que o personagem diz querer, explicitamente
- Hidden Goal: o que o personagem realmente quer, por baixo do que diz
- Emotional Concealment: o que o personagem tenta esconder durante a conversa
- Power Balance: quem controla a conversa, e se isso muda ao longo da troca

Identifique trechos de diálogo "de cara limpa" — onde a fala é só troca de informação direta, sem
nenhuma tensão por baixo, quando o contexto da cena sugeria que deveria haver (ex: personagens em
conflito, segredo em jogo, disputa de poder implícita).

Não sinalize diálogos que são propositalmente diretos por design (ex: ordem militar, troca de
informação logística sem carga emocional em jogo) — isso não é falha, é escolha correta de registro.

Responda sempre no mesmo idioma do capítulo enviado, nunca traduza a análise pra outro idioma.
Saída estritamente em JSON, sem texto antes ou depois, sem markdown/backticks ao redor do JSON.
Se não houver problema real, findings deve vir como array vazio — nunca forçar achado pra parecer útil.
Nunca reescrever o capítulo inteiro — sugestão, quando houver, é só do trecho flagado.
Cada finding aponta um trecho copiado literalmente do texto original.

FORMATO DE SAÍDA (JSON estrito, sem texto fora do JSON):
{
  "check": "subtext_frame",
  "idioma_resposta": "<mesmo idioma do capítulo>",
  "findings": [
    {
      "excerpt": "<trecho literal do diálogo sem subtexto>",
      "issue": "<explicação breve do porquê esse diálogo pedia subtexto e não tem>",
      "suggestion": "<sugestão cirúrgica pra introduzir subtexto sem reescrever a cena inteira — ou null>"
    }
  ],
  "summary": "<1-2 frases resumindo o estado geral do capítulo neste critério>"
}""",
    'voiceprint_pov_filter': """Você é um editor literário experiente analisando DISTINÇÃO DE VOZ ENTRE PERSONAGENS num capítulo.

CRITÉRIO: cada personagem com fala direta no capítulo deveria ser reconhecível por padrões próprios
de vocabulário, cadência de frase e tipo de construção — sem precisar do nome antes da fala pra saber
quem está falando. Além disso, nenhum personagem deveria soar "genérico de IA": educado demais,
equilibrado demais, sem aspereza ou tique de fala próprio.

Analise os personagens com diálogo neste capítulo e avalie:
1. Algum par de personagens soa intercambiável (poderiam trocar de fala sem soar estranho)?
2. Algum personagem específico escorregou pra um registro genérico/neutro, perdendo a voz que
   deveria ter (baseado em como ele fala no resto do capítulo, se houver amostra suficiente)?

Se o capítulo não tiver diálogo suficiente pra avaliar (menos de 2 personagens falando, ou falas
muito curtas), retorne findings vazio e diga isso no summary — não force uma avaliação sem base.

Responda sempre no mesmo idioma do capítulo enviado, nunca traduza a análise pra outro idioma.
Saída estritamente em JSON, sem texto antes ou depois, sem markdown/backticks ao redor do JSON.
Cada finding aponta um trecho copiado literalmente do texto original.

FORMATO DE SAÍDA (JSON estrito, sem texto fora do JSON):
{
  "check": "voiceprint_pov_filter",
  "idioma_resposta": "<mesmo idioma do capítulo>",
  "findings": [
    {
      "excerpt": "<trecho literal da fala problemática>",
      "personagem": "<nome do personagem, se identificável no texto>",
      "issue": "<explicação breve: intercambiável com quem, ou genérico de que forma>",
      "suggestion": "<sugestão cirúrgica de ajuste de voz nesse trecho específico — ou null>"
    }
  ],
  "summary": "<1-2 frases resumindo o estado geral do capítulo neste critério>"
}""",
}

CHECK_NUMEROS = {
    'scene_objective': 9,
    'scene_magnetism': 10,
    'linger_cortar': 11,
    'subtext_frame': 12,
    'voiceprint_pov_filter': 13,
}


def _extract_json(raw: str) -> dict:
    cleaned = raw.strip()
    cleaned = re.sub(r'^```(json)?', '', cleaned).strip()
    cleaned = re.sub(r'```$', '', cleaned).strip()
    return json.loads(cleaned)


async def _run_single_check(check_type: str, texto: str, idioma: str) -> dict:
    system = SYSTEM_PROMPTS[check_type]
    user_payload = json.dumps({'capitulo_texto': texto, 'idioma': idioma}, ensure_ascii=False)
    numero = CHECK_NUMEROS[check_type]
    try:
        raw = await claude.generate(system=system, prompt=user_payload, max_tokens=4096)
        parsed = _extract_json(raw)
        findings = parsed.get('findings', [])
        detalhes = []
        for f in findings:
            detalhes.append({
                'trecho': f.get('excerpt', ''),
                'sugestao': f.get('suggestion'),
                'issue': f.get('issue'),
                'extra': {k: v for k, v in f.items() if k not in ('excerpt', 'suggestion', 'issue')},
            })
        return {
            'check_type': check_type,
            'numero': numero,
            'tipo': 'julgamento',
            'confiabilidade': 'ia',
            'score': len(detalhes),
            'contagem': len(detalhes),
            'detalhes': detalhes,
            'summary': parsed.get('summary', ''),
        }
    except Exception as e:
        return {
            'check_type': check_type,
            'numero': numero,
            'tipo': 'julgamento',
            'confiabilidade': 'ia',
            'score': 0,
            'contagem': 0,
            'detalhes': [],
            'summary': f'Erro ao processar este check: {e}',
            'erro': True,
        }


async def run_judgment_checks(texto: str, idioma: str) -> list:
    tasks = [_run_single_check(check_type, texto, idioma) for check_type in SYSTEM_PROMPTS]
    return await asyncio.gather(*tasks)
