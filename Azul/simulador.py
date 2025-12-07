# simulator.py
"""
Simula múltiplas partidas CPU x CPU usando os agentes do ai_agents.py
Exemplo de uso:
    python simulator.py --games 50 --p1 greedy --p2 mcts
"""

import argparse
import random
from jogo import Jogo
from main import Jogador as JogadorMain  # se main.Jogador existe; sua classe Jogador real está em jogador.py -> import diferente
# Para evitar confusão, import a classe Jogador base do seu modulo jogador
from jogador import Jogador
from ai_agents import GreedyAgent, MinimaxAgent, MCTSAgent, clone_game
from jogo import Jogo

AGENTS_MAP = {
    "greedy": GreedyAgent,
    "minimax": MinimaxAgent,
    "mcts": MCTSAgent,
    "cpu": Jogador,  # fallback: uso do Jogador padrão que já implementa _escolha_cpu
}

def criar_agente(nome_tipo, nome_instancia):
    Tipo = AGENTS_MAP.get(nome_tipo.lower())
    if Tipo is None:
        raise ValueError(f"Tipo desconhecido: {nome_tipo}")
    # para Jogador padrão, construa com tipo "cpu"
    if Tipo is Jogador:
        return Jogador(nome_instancia, tipo="cpu")
    else:
        # instanciar com parâmetros padrão (pode ajustar)
        if Tipo is GreedyAgent:
            return GreedyAgent(nome_instancia)
        if Tipo is MinimaxAgent:
            return MinimaxAgent(nome_instancia)
        if Tipo is MCTSAgent:
            return MCTSAgent(nome_instancia)
        return Tipo(nome_instancia, tipo="cpu")

def run_single_game(agent_types, seed=None, verbose=False):
    """
    agent_types: list of strings (ex: ["greedy","minimax"])
    """
    if seed is not None:
        random.seed(seed)
    jogadores = []
    for i, t in enumerate(agent_types):
        jogadores.append(criar_agente(t, f"{t.upper()}_{i+1}"))

    jogo = Jogo(jogadores)
    # Para que os agentes que precisam do objeto Jogo durante escolha_jogada possam acessá-lo,
    # alteramos temporariamente o processo de jogo para incluir "game" no estado passado a escolher_jogada.
    # Em Jogo.fase_coleta, estado contém expositores, centro, jogadores, indice_jogador, all_colors
    # Vamos rodar manualmente a fase de coleta aqui para injetar game no estado.

    jogo.preparar_rodada()
    # loop de rodadas até terminar
    while True:
        # fase coleta manual (similar à Jogo.fase_coleta)
        # manter owner_first_token etc conforme implementação original
        start_idx = 0
        if jogo.owner_first_token is not None:
            try:
                start_idx = jogo.jogadores.index(jogo.owner_first_token)
            except ValueError:
                start_idx = 0

        turno_offset = 0
        while not jogo._todas_fontes_vazias():
            jogador = jogo.jogadores[(start_idx + turno_offset) % len(jogo.jogadores)]
            estado = {
                "expositores": jogo.expositores,
                "centro": jogo.centro,
                "jogadores": jogo.jogadores,
                "indice_jogador": (start_idx + turno_offset) % len(jogo.jogadores),
                "all_colors": jogo.all_colors,
                "game": jogo  # injetado para agentes que o utilizam
            }
            escolha = jogador.escolher_jogada(estado)
            if escolha is None:
                turno_offset += 1
                continue
            jogo._aplicar_escolha(jogador, escolha)
            turno_offset += 1

        # fase parede e pontuação (usa game internamente)
        jogo.fase_parede_e_pontuacao()

        # verificar fim de jogo (reutilizamos método)
        if jogo.jogo_terminou():
            break

        # preparar próxima rodada
        jogo.preparar_rodada()

    # fim de jogo
    jogo.aplicar_bonificacoes_finais()
    # retornar pontuação
    return [(j.nome, j.pontos) for j in jogo.jogadores]

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=10, help="Qtd de partidas")
    p.add_argument("--p1", type=str, default="greedy")
    p.add_argument("--p2", type=str, default="mcts")
    p.add_argument("--seed", type=int, default=None)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    results = []
    for i in range(args.games):
        seed = None if args.seed is None else args.seed + i
        scores = run_single_game([args.p1, args.p2], seed=seed)
        results.append(scores)
        print(f"Game {i+1}: {scores}")
    # sumarizar
    wins = {args.p1:0, args.p2:0, "tie":0}
    for s in results:
        if s[0][1] > s[1][1]:
            wins[args.p1] += 1
        elif s[1][1] > s[0][1]:
            wins[args.p2] += 1
        else:
            wins["tie"] += 1
    print("Resumo:", wins)
