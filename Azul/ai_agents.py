# ai_agents.py
"""
Agentes IA para Azul: Greedy, Minimax (simples) e MCTS (simples).
Cada agente é uma subclasse de jogador.Jogador e sobrescreve escolher_jogada.
Não altera nenhum outro módulo do seu projeto.
"""

import copy
import math
import random
import time
from jogador import Jogador
from tabuleiro import Tabuleiro
from jogo import Jogo
from azulejos import CorAzulejo

# ---------- Helpers ----------

def clone_game(game):
    """Deep copy do objeto Jogo (usa copy.deepcopy)."""
    return copy.deepcopy(game)

def avaliar_jogo_simples(game, jogador_idx):
    """
    Heurística de avaliação simples:
    - pontos atuais do jogador
    - + 1 por peça colocada na parede
    - + 0.5 por peça em linhas padrão (mais provável se completar)
    - - penalidades do piso (contadas como negativas na pontuação atual)
    Observação: heurística simples e rápida — pode ser substituída por algo mais sofisticado.
    """
    jogador = game.jogadores[jogador_idx]
    score = jogador.pontos
    # contar peças já na parede
    cnt_wall = sum(1 for r in range(5) for c in range(5) if jogador.tabuleiro.parede[r][c] is not None)
    cnt_lines = sum(len(l) for l in jogador.tabuleiro.linhas)
    # less weight for lines, more for wall
    score += 1.0 * cnt_wall + 0.5 * cnt_lines
    # penalty approximate from floor
    floor_penalty = 0
    for idx, az in enumerate(jogador.tabuleiro.piso):
        # floor tokens in your implementation stored as "TOKEN" or tiles
        # use approximate weights
        if az == "TOKEN":
            floor_penalty += 1.0  # token implies extra penalty
        else:
            # index weight unknown here; just -0.5
            floor_penalty += 0.5
    score -= floor_penalty
    return score

def gerar_opcoes_para_jogador(game, jogador_idx):
    """
    Retorna lista de opções legais no formato:
    (fonte, idx or None, cor, linha)
    fonte: "expositor" ou "centro"
    idx: expositor index (0-based) ou None
    cor: CorAzulejo
    linha: 0..4 or -1 para piso
    """
    jogador = game.jogadores[jogador_idx]
    expositores = game.expositores
    centro = game.centro

    opcoes = []
    # expositores
    for i, e in enumerate(expositores):
        if e.vazio():
            continue
        cores = e.cores_disponiveis()
        for cor in cores:
            # para cada linha possível para este jogador
            linhas_validas = [r for r in range(5) if jogador.tabuleiro.pode_colocar_na_linha(r, cor)]
            if not linhas_validas:
                opcoes.append(("expositor", i, cor, -1))
            else:
                for ln in linhas_validas:
                    opcoes.append(("expositor", i, cor, ln))
    # centro
    if centro.azulejos or centro.token_primeiro:
        cores = centro.cores_disponiveis()
        for cor in cores:
            linhas_validas = [r for r in range(5) if jogador.tabuleiro.pode_colocar_na_linha(r, cor)]
            if not linhas_validas:
                opcoes.append(("centro", None, cor, -1))
            else:
                for ln in linhas_validas:
                    opcoes.append(("centro", None, cor, ln))
    # se nenhuma opção (teoricamente não acontece), deixe None
    return opcoes

def aplicar_escolha_simulada(game, jogador_idx, escolha):
    """
    Aplica a escolha ao game (mutates game). Reusa _aplicar_escolha do Jogo
    mas como é método "privado" no seu Jogo, replicamos a lógica mínima aqui.
    Para manter compatibilidade, chamamos game._aplicar_escolha se existir.
    """
    # se a classe Jogo expõe _aplicar_escolha, podemos usá-la (mantive compatibilidade)
    try:
        jogador = game.jogadores[jogador_idx]
        # adaptar o formato que Jogo._aplicar_escolha espera: jogador (objeto) e escolha (dict)
        game._aplicar_escolha(jogador, escolha)
    except Exception:
        # fallback: tentativa manual (menos ideal)
        fonte = escolha["fonte"]
        cor = escolha["cor"]
        linha = escolha["linha"]
        jogador = game.jogadores[jogador_idx]
        escolhidos = []
        took_token = False

        if fonte[0] == "expositor":
            idx = fonte[1]
            escolhidos, resto = game.expositores[idx].retirar_cor(cor)
            if resto:
                game.centro.adicionar(resto)
        else:
            escolhidos, took_token = game.centro.retirar_cor(cor)
            if took_token:
                if game.owner_first_token is None:
                    game.owner_first_token = jogador

        if linha == -1:
            jogador.tabuleiro.piso += escolhidos
        else:
            jogador.tabuleiro.adicionar_a_linha(linha, escolhidos, to_floor_if_excess=True)

        if took_token:
            jogador.tabuleiro.piso.append("TOKEN")

# ---------- Agentes ----------

class GreedyAgent(Jogador):
    """
    Greedy via simulações rápidas:
    Para cada opção legal, simula N playouts (jogadores adversários jogam com heurística aleatória/greedy)
    e escolhe a opção com maior média de pontos obtidos ao final da rodada.
    """

    def __init__(self, nome, tipo="cpu", sim_per_option=12, opponent_policy="greedy"):
        super().__init__(nome, tipo=tipo)
        self.sim_per_option = sim_per_option
        self.opponent_policy = opponent_policy

    def escolher_jogada(self, estado):
        # construir um Game "simulado" a partir do estado
        # estado contém expositores e centro - mas não contem objeto Jogo completo.
        # Para simular, vamos esperar que exista um Jogo em estado["game"] (simulator passa isso).
        game = estado.get("game")
        me_idx = estado.get("indice_jogador", 0)
        if game is None:
            # fallback: use the lightweight cpu from Jogador
            return super()._escolha_cpu(estado)

        opcoes = gerar_opcoes_para_jogador(game, me_idx)
        if not opcoes:
            return None

        best = None
        best_score = -float("inf")
        for opc in opcoes:
            total = 0.0
            for _ in range(self.sim_per_option):
                g = clone_game(game)
                aplicar_escolha_simulada(g, me_idx, {"fonte": (opc[0], opc[1]), "cor": opc[2], "linha": opc[3]})
                # continuar a rodada com políticas simples até esgotar fontes
                # (faremos jogadores na ordem circular a partir do próximo)
                # rollout: outros jogadores usam greedy-like quick policy
                rollout_players = list(range(len(g.jogadores)))
                # a rodada continua com a ordem circular a partir do jogador após me_idx
                next_offset = 1
                while not g._todas_fontes_vazias():
                    current_idx = (me_idx + next_offset) % len(g.jogadores)
                    # skip if current player has no legal options (shouldn't happen normally)
                    choices = gerar_opcoes_para_jogador(g, current_idx)
                    if not choices:
                        next_offset += 1
                        continue
                    # pick a choice according to opponent_policy
                    if self.opponent_policy == "greedy":
                        # choose option that maximizes quick heuristic after applying
                        bestc = None
                        bestv = -float("inf")
                        for c in choices:
                            gg = clone_game(g)
                            aplicar_escolha_simulada(gg, current_idx, {"fonte": (c[0], c[1]), "cor": c[2], "linha": c[3]})
                            v = avaliar_jogo_simples(gg, current_idx)
                            if v > bestv:
                                bestv = v
                                bestc = c
                        escolha = {"fonte": (bestc[0], bestc[1]), "cor": bestc[2], "linha": bestc[3]}
                    else:
                        escolha = {"fonte": (choices[0][0], choices[0][1]), "cor": choices[0][2], "linha": choices[0][3]}
                    aplicar_escolha_simulada(g, current_idx, escolha)
                    next_offset += 1
                # finalizar rodada para computar pontos ganhos
                # usamos fase_parede_e_pontuacao do jogo para que pontos sejam aplicados
                # observe que fase_parede_e_pontuacao aplica para todos jogadores e usa saco.descartar etc.
                g.fase_parede_e_pontuacao()
                total += g.jogadores[me_idx].pontos
            avg = total / max(1, self.sim_per_option)
            if avg > best_score:
                best_score = avg
                best = opc
        fonte = (best[0], best[1])
        return {"fonte": fonte, "cor": best[2], "linha": best[3]}


class MinimaxAgent(Jogador):
    """
    Minimax limitado com poda alfa-beta para decisões locais:
    - Considera apenas a rodada atual (não gera novas rodadas nem reembaralha o saco).
    - Depth limitado (padrão 2 ply: eu -> adversário).
    - Em nós chance (se houver escolhas com incerteza) usamos amostragem aleatória.
    Observação: é uma aproximação e é relativamente custosa; limite de profundidade recomendado 2-3.
    """

    def __init__(self, nome, tipo="cpu", depth=2, samples_per_chance=3):
        super().__init__(nome, tipo=tipo)
        self.depth = depth
        self.samples = samples_per_chance

    def escolher_jogada(self, estado):
        game = estado.get("game")
        me_idx = estado.get("indice_jogador", 0)
        if game is None:
            return super()._escolha_cpu(estado)

        def minimax(g, current_idx, depth, alpha, beta, maximizing_idx):
            """
            Retorna valor heurístico para jogador maximizing_idx.
            current_idx: índice do jogador que joga no nó atual.
            """
            if depth == 0 or g._todas_fontes_vazias():
                return avaliar_jogo_simples(g, maximizing_idx)

            # gerar opções do current_idx
            opts = gerar_opcoes_para_jogador(g, current_idx)
            if not opts:
                # pular para o próximo jogador
                next_idx = (current_idx + 1) % len(g.jogadores)
                return minimax(g, next_idx, depth, alpha, beta, maximizing_idx)

            if current_idx == maximizing_idx:
                value = -float("inf")
                for o in opts:
                    gg = clone_game(g)
                    aplicar_escolha_simulada(gg, current_idx, {"fonte": (o[0], o[1]), "cor": o[2], "linha": o[3]})
                    next_idx = (current_idx + 1) % len(gg.jogadores)
                    v = minimax(gg, next_idx, depth-1, alpha, beta, maximizing_idx)
                    if v > value:
                        value = v
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
                return value
            else:
                # minimizing (opponent) - assume they minimize our heuristic
                value = float("inf")
                for o in opts:
                    gg = clone_game(g)
                    aplicar_escolha_simulada(gg, current_idx, {"fonte": (o[0], o[1]), "cor": o[2], "linha": o[3]})
                    next_idx = (current_idx + 1) % len(gg.jogadores)
                    v = minimax(gg, next_idx, depth-1, alpha, beta, maximizing_idx)
                    if v < value:
                        value = v
                    beta = min(beta, value)
                    if beta <= alpha:
                        break
                return value

        # escolher melhor jogada executando minimax para cada opção do jogador atual
        opcoes = gerar_opcoes_para_jogador(game, me_idx)
        if not opcoes:
            return None
        best = None
        bestval = -float("inf")
        for o in opcoes:
            gg = clone_game(game)
            aplicar_escolha_simulada(gg, me_idx, {"fonte": (o[0], o[1]), "cor": o[2], "linha": o[3]})
            next_idx = (me_idx + 1) % len(gg.jogadores)
            v = minimax(gg, next_idx, self.depth-1, -float("inf"), float("inf"), me_idx)
            if v > bestval:
                bestval = v
                best = o
        fonte = (best[0], best[1])
        return {"fonte": fonte, "cor": best[2], "linha": best[3]}


class MCTSAgent(Jogador):
    """
    MCTS simples:
    - Cada decisão executa N iterações de MCTS.
    - Rollout policy: greedy quick (avaliar_jogo_simples) ou aleatório.
    - Tree keyed by deep-copied game state (repr of board).
    Limitações: para manter simplicidade e compatibilidade com o seu Jogo, a árvore é reconstruída a cada decisão.
    """

    class Node:
        def __init__(self, parent, move):
            self.parent = parent
            self.move = move  # move that led to this node from parent
            self.children = []
            self.visits = 0
            self.value = 0.0

    def __init__(self, nome, tipo="cpu", iterations=200, rollout_limit=200):
        super().__init__(nome, tipo=tipo)
        self.iterations = iterations
        self.rollout_limit = rollout_limit
        random.seed()

    def escolher_jogada(self, estado):
        game = estado.get("game")
        me_idx = estado.get("indice_jogador", 0)
        if game is None:
            return super()._escolha_cpu(estado)

        root = MCTSAgent.Node(parent=None, move=None)

        legal_moves = gerar_opcoes_para_jogador(game, me_idx)
        if not legal_moves:
            return None

        # map moves to child nodes
        move_nodes = {i: MCTSAgent.Node(parent=root, move=legal_moves[i]) for i in range(len(legal_moves))}
        root.children = list(move_nodes.values())

        def rollout_simulation(g, starting_idx):
            # play the rest of the round with quick greedy heuristic
            me_local_idx = me_idx
            while not g._todas_fontes_vazias():
                cur = starting_idx % len(g.jogadores)
                choices = gerar_opcoes_para_jogador(g, cur)
                if not choices:
                    starting_idx += 1
                    continue
                # pick greedy quick
                bestc = None
                bestv = -float("inf")
                for c in choices:
                    gg = clone_game(g)
                    aplicar_escolha_simulada(gg, cur, {"fonte": (c[0], c[1]), "cor": c[2], "linha": c[3]})
                    v = avaliar_jogo_simples(gg, cur)
                    if v > bestv:
                        bestv = v
                        bestc = c
                aplicar_escolha_simulada(g, cur, {"fonte": (bestc[0], bestc[1]), "cor": bestc[2], "linha": bestc[3]})
                starting_idx += 1
            # finalize round and return score for me_idx
            g.fase_parede_e_pontuacao()
            return g.jogadores[me_local_idx].pontos

        # MCTS iterations
        for it in range(self.iterations):
            # selection: pick a child at root via UCB
            # for deeper trees we would walk down; here root->child only because we rebuild tree per decision
            # choose child with highest UCB
            total_visits = sum(c.visits for c in root.children) + 1
            best_child = None
            best_ucb = -float("inf")
            for child in root.children:
                if child.visits == 0:
                    ucb = float("inf")
                else:
                    exploit = child.value / child.visits
                    explore = math.sqrt(2 * math.log(total_visits) / child.visits)
                    ucb = exploit + 1.41 * explore
                if ucb > best_ucb:
                    best_ucb = ucb
                    best_child = child

            # expansion & simulation
            move = best_child.move
            g = clone_game(game)
            aplicar_escolha_simulada(g, me_idx, {"fonte": (move[0], move[1]), "cor": move[2], "linha": move[3]})
            next_start = (me_idx + 1) % len(g.jogadores)
            # rollout
            score = rollout_simulation(g, next_start)

            # backpropagate
            node = best_child
            while node is not None:
                node.visits += 1
                node.value += score
                node = node.parent

        # choose child with max average value
        best_i = None
        best_avg = -float("inf")
        for i, child in enumerate(root.children):
            if child.visits == 0:
                avg = -float("inf")
            else:
                avg = child.value / child.visits
            if avg > best_avg:
                best_avg = avg
                best_i = i

        chosen = legal_moves[best_i]
        fonte = (chosen[0], chosen[1])
        return {"fonte": fonte, "cor": chosen[2], "linha": chosen[3]}
