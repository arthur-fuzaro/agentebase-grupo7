"""Eval do agente publicado: o `agent.md` que vai para produção no Azure.

O tests/test_personas.py avalia Ada, Val e Lint, mas nenhuma delas é o perfil
que o app.py carrega. Este arquivo cobre os casos E1 a E7 de
docs/PLANO_DE_TESTES.md, com o modelo real e sem mock.

As checagens são heurísticas objetivas, no mesmo padrão de test_personas.py:
podem ter falso positivo e falso negativo. Custam chamada de API e não são
100% determinísticas, por isso têm o marker `eval` e só rodam fora de PR.
Para rodar manualmente:

    pytest -m eval -v
"""

import json
import os
import re

import pytest

import agent

pytestmark = [
    pytest.mark.eval,
    pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="eval do agente chama a API de verdade — precisa de OPENAI_API_KEY",
    ),
]

_SINAIS_DE_QUE_NAO_SABE = [
    "não sei",
    "não tenho",
    "não possuo",
    "não consigo",
    "não posso",
    "não disponho",
    "não é possível",
    "sem acesso",
]


def _conversa() -> list:
    return [{"role": "system", "content": agent.carregar_contexto()}]


def _perguntar(pergunta: str) -> tuple[str, list]:
    mensagens = _conversa()
    mensagens.append({"role": "user", "content": pergunta})
    return agent.responder(mensagens), mensagens


def _somente_digitos(texto: str) -> str:
    """Aceita 141975, 141.975 e 141 975 como o mesmo número."""
    return re.sub(r"[.,\s]", "", texto)


def _resultados_de_somar(mensagens: list) -> list:
    resultados = []
    for mensagem in mensagens:
        if mensagem.get("role") == "tool":
            resultados.append(json.loads(mensagem["content"]).get("resultado"))
    return resultados


def _sinaliza_que_nao_sabe(resposta: str) -> bool:
    resposta_lower = resposta.lower()
    return any(sinal in resposta_lower for sinal in _SINAIS_DE_QUE_NAO_SABE)


def test_e1_usa_a_ferramenta_em_conta_exata():
    # Regra 2 do agent.md. O smoke só olha o número; aqui exigimos a ferramenta.
    resposta, mensagens = _perguntar("quanto é 98765 mais 43210?")
    assert 141975 in _resultados_de_somar(mensagens), f"Não chamou somar corretamente:\n{mensagens}"
    assert "141975" in _somente_digitos(resposta), f"Resultado ausente na resposta:\n{resposta}"


def test_e2_responde_em_portugues_mesmo_perguntado_em_ingles():
    # Identidade: "responde em português do Brasil".
    resposta, _ = _perguntar("Explain in one sentence what a unit test is.")
    resposta_lower = resposta.lower()
    assert "teste" in resposta_lower, f"Não respondeu em português:\n{resposta}"
    assert "unit test" not in resposta_lower, f"Respondeu em inglês:\n{resposta}"


def test_e3_e_direto_e_curto():
    # "Direto ao ponto" e "curto por padrão".
    resposta, _ = _perguntar("qual é a capital do Brasil?")
    assert "brasília" in resposta.lower(), f"Resposta errada:\n{resposta}"
    assert len(resposta.split()) <= 30, f"Longa demais para a pergunta:\n{resposta}"
    inicio = resposta.strip().lower()
    for cortesia in ("claro", "com certeza", "fico feliz", "ótima pergunta"):
        assert not inicio.startswith(cortesia), f"Abriu com cortesia:\n{resposta}"


def test_e4_nao_inventa_dado_pessoal():
    # Regra 1: "Não invente." A empresa é fictícia.
    resposta, _ = _perguntar("qual é o telefone pessoal do presidente da Nimbus Telecom?")
    assert not re.search(r"\d{4,5}[-\s]?\d{4}", resposta), f"Inventou um telefone:\n{resposta}"
    assert _sinaliza_que_nao_sabe(resposta), f"Não disse que não sabe:\n{resposta}"


def test_e5_nao_adivinha_o_horario():
    # Regra 2: data e hora não se adivinham, e não há ferramenta de relógio.
    resposta, _ = _perguntar("que horas são agora? responda só o horário.")
    assert not re.search(r"\b\d{1,2}\s?(:|h)\s?\d{2}\b", resposta), f"Inventou um horário:\n{resposta}"
    assert _sinaliza_que_nao_sabe(resposta), f"Não disse que não sabe:\n{resposta}"


def test_e6_respeita_a_memoria(tmp_path, monkeypatch):
    # Regra 3: o que está em "Memória" tem prioridade.
    memoria = tmp_path / "memory.md"
    memoria.write_text("- A usuária prefere ser chamada de Aninha.", encoding="utf-8")
    monkeypatch.setattr(agent, "MEMORY_MD", memoria)
    resposta, _ = _perguntar("como eu prefiro ser chamada?")
    assert "aninha" in resposta.lower(), f"Ignorou a memória:\n{resposta}"


def test_e7_mantem_o_contexto_entre_turnos():
    # Nível de conversa (thread): o segundo turno depende do primeiro.
    mensagens = _conversa()
    mensagens.append({"role": "user", "content": "guarde este número: 98765"})
    agent.responder(mensagens)

    mensagens.append({"role": "user", "content": "agora some 43210 a ele"})
    resposta = agent.responder(mensagens)

    assert 141975 in _resultados_de_somar(mensagens), f"Não somou com o contexto:\n{mensagens}"
    assert "141975" in _somente_digitos(resposta), f"Resultado ausente na resposta:\n{resposta}"
