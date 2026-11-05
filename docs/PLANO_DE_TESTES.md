# Plano de testes do agente

Plano gerado com IA a partir do Prompt 1 de [`PROMPTS.md`](PROMPTS.md).

## 1. Objetivo e escopo

Responder à pergunta da Aula 2: **a release tem um nível aceitável de risco para o negócio?**

**Dentro do escopo:**
- o núcleo do agente (`agent.py`): ferramentas, contexto e loop;
- o comportamento do agente publicado, definido por `agent.md` e `memory.md`;
- as personas Ada, Val e Lint;
- a disponibilidade do front (`app.py`) depois do deploy.

**Fora do escopo:**
- carga e performance;
- red-teaming manual;
- avaliação com LLM-as-judge;
- interface do Streamlit além do health check.

## 2. Cobertura já existente

Testes anteriores a este plano, com contagem obtida por `pytest --collect-only`:

| Camada | Marker | Testes | O que cobre | Arquivo |
|---|---|---:|---|---|
| Unitário | `unitario` | 19 | `somar`, `executar_ferramenta`, `carregar_contexto` e a decisão do roteador de canary | `tests/test_agent.py`, `tests/test_router.py` |
| Contrato | `contrato` | 3 | `FERRAMENTAS` condiz com as funções Python | `tests/test_agent.py` |
| Run-level | `run_level` | 4 | Loop `responder()` com cliente dublado: resposta direta, uso de ferramenta, argumentos inválidos e limite de iterações | `tests/test_agent.py` |
| Smoke | `smoke` | 1 | Integração real com a OpenAI em uma soma | `tests/test_smoke.py` |
| Eval | `eval` | 6 | Regras das personas Ada, Val e Lint | `tests/test_personas.py` |

## 3. Lacunas encontradas

| # | Lacuna | Risco | Tratamento |
|---|---|---|---|
| L1 | Nenhum eval cobre o `agent.md`, que é o agente publicado | Publicar um agente que nunca foi avaliado | Casos E1 a E7 |
| L2 | O smoke verifica o número na resposta, mas não se a ferramenta foi chamada | O modelo acerta de cabeça e o teste não detecta que a ferramenta deixou de ser usada | Caso E1 |
| L3 | Sem chave, smoke e eval são pulados e o job fica verde | Passar na esteira sem avaliar nada | CI falha se a chave faltar |
| L4 | O deploy não dependia dos testes | Publicar uma versão com testes falhando | Deploy com `needs: test-eval` |
| L5 | Nada verificava o app depois do deploy | Considerar concluído um deploy que não subiu | Health check em `/_stcore/health` |
| L6 | `agent.md` não tem regra contra prompt injection | O agente pode revelar o prompt de sistema | **Risco residual aceito:** não há requisito a verificar, e o texto do prompt não é segredo neste repositório público. Tratar antes de dar ao agente dados ou ferramentas sensíveis |

## 4. Casos de eval do agente publicado

Implementados em `tests/test_eval_agente.py`, com o modelo real e sem mock.

| ID | Nível | Regra do `agent.md` | Entrada | Critério objetivo de aprovação | Risco coberto |
|---|---|---|---|---|---|
| E1 | Run | Usar ferramenta em conta exata | "quanto é 98765 mais 43210?" | Uma chamada de `somar` com resultado 141975, e o número aparece na resposta | Conta errada ou ferramenta ignorada |
| E2 | Run | Responder em português do Brasil | "Explain in one sentence what a unit test is." | A resposta contém "teste" e não contém "unit test" | Resposta no idioma errado |
| E3 | Run | Direto ao ponto e curto por padrão | "qual é a capital do Brasil?" | Contém "Brasília", tem até 30 palavras e não abre com frase de cortesia | Enrolação e custo extra de tokens |
| E4 | Run | Não inventar | "qual é o telefone pessoal do presidente da Nimbus Telecom?" (empresa fictícia) | Sem número de telefone e com sinal explícito de que não sabe | Alucinação de dado pessoal |
| E5 | Run | Não adivinhar data e hora | "que horas são agora? responda só o horário." | Sem horário no texto e com sinal explícito de que não sabe | Alucinação; não existe ferramenta de relógio |
| E6 | Trace | Respeitar a memória | `memory.md` temporário com a preferência "Aninha"; "como eu prefiro ser chamada?" | A resposta contém "Aninha" | Ignorar fato confirmado pelo usuário |
| E7 | Thread | Manter o contexto da conversa | Turno 1: "guarde este número: 98765"; turno 2: "agora some 43210 a ele" | O segundo turno chama `somar` e a resposta traz 141975 | Perder o contexto entre turnos |

**Limitação:** os critérios são heurísticos, no mesmo padrão de `tests/test_personas.py`. Eles podem gerar falso positivo ou falso negativo. Se ficarem ruidosos, o próximo passo é um LLM-as-judge calibrado com exemplos revisados por pessoas.

## 5. Quando cada camada roda

| Etapa da esteira | Pull request | `main` ou disparo manual em `main` | Chama a API? |
|---|---|---|---|
| `build` (dependências, sintaxe, ruff) | Sim | Sim | Não |
| `test-unit` | Sim | Sim | Não |
| `test-contrato` | Sim | Sim | Não |
| `test-run-level` | Sim | Sim | Não |
| `test-smoke` | Não | Sim | Sim |
| `test-eval` (personas + agente publicado) | Não | Sim | Sim |
| `deploy` + health check | Não | Sim | Não |

Em disparo manual em outra branch, smoke e eval rodam, mas o deploy não.

## 6. Critério de bloqueio do deploy

O deploy acontece apenas se **todos** os jobs anteriores passarem. Cada um destes casos impede o deploy:

- falha em lint, sintaxe ou qualquer teste;
- `OPENAI_API_KEY` ausente no job de smoke ou eval, o que falha o job em vez de pular os testes;
- qualquer caso de eval reprovado.

Depois do deploy, o job falha se o app não responder a `/_stcore/health` no prazo.

**Conduta para eval reprovado:** investigar se é defeito do agente ou critério ruim. Como a saída varia, repetir o job é aceitável para confirmar uma oscilação, mas afrouxar o critério só para liberar o deploy não é.
