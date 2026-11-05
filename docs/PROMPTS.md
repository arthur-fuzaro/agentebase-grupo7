# Prompts utilizados

Registro literal dos prompts usados para gerar o plano de testes e os evals.

- **Ferramenta:** Claude Code
- **Modelo:** Claude Opus 5.5 (`claude-opus-5-5`)
- **Data:** 2026-11-04
- **Como foram usados:** na mesma sessão de trabalho, com acesso aos arquivos do repositório. Os prompts foram definidos no plano aprovado antes da geração.

## Prompt 1: plano de testes

**Resultado:** [`PLANO_DE_TESTES.md`](PLANO_DE_TESTES.md)

```text
Você é engenheiro de QA de agentes de IA. Analise `agent.py`, `agent.md`, `app.py`, a pasta `tests/` e `.github/workflows/ci.yml` deste repositório. Escreva um plano de testes unitários e de eval com: objetivo e escopo; mapa do que já está coberto, sem inventar cobertura; lacunas; casos de eval do agente publicado (`agent.md`), cada um com entrada, critério objetivo de aprovação e risco coberto; quando cada camada roda na esteira; e o critério que bloqueia o deploy.
```

## Prompt 2: implementação dos evals

**Resultado:** [`tests/test_eval_agente.py`](../tests/test_eval_agente.py)

```text
Implemente em `tests/test_eval_agente.py` os casos de eval do plano, com marker `eval`, chamando o modelo real, sem mock e com critérios objetivos, seguindo o padrão de `tests/test_personas.py`.
```

## O que estes prompts não geraram

Os testes unitários, de contrato, run-level, smoke e os evals das personas já existiam no repositório antes destes prompts. O plano os trata como cobertura mapeada.

<!-- Se o grupo tiver os prompts originais do PR #8 (feature/testes-agente), inclua-os aqui, literalmente. -->
