# ai.py
import copy
import math
import random
from typing import Optional

# Importe os tipos do seu engine
from jogo import JogoAzul, Acao
from azuleijos import Cor

# ----------------------------
# Greedy AI (busca gulosa)
# ----------------------------
class GreedyAI:
    """
    Escolhe a ação que maximiza uma função heurística de valor imediato.
    Avaliação: ganho de pontos esperado imediatamente após executar a ação
    (inclui penalidade do chão). Também considera ganho potencial por completar linhas.
    """
    def __init__(self, preferencia_empate_random=True):
        self.pref_random = preferencia_empate_random

    def escolher_acao(self, jogo: JogoAzul) -> Optional[Acao]:
        acoes = jogo.obter_acoes_legais()
        if not acoes:
            return None
        best_val = -1e9
        best_actions = []
        for ac in acoes:
            # simular
            sim = copy.deepcopy(jogo)
            sim.executar_acao(copy.deepcopy(ac))
            # se ação fecha rodada: sim._finalizar_rodada() já será chamada internamente
            # computar avaliação simples: diferença de pontuação entre jogador antes e depois
            # precisamos medir a pontuação do jogador que jogou (o predecessor index)
            # deduzimos o index do jogador que aplicou a ação: no engine, jogador_atual avança após executar_acao;
            # então jogador anterior é (estado.jogador_atual -1) mod n
            # Para avaliação imediata, comparamos pontuação desse jogador no sim com no jogo original
            jogador_idx = (jogo.estado.jogador_atual) % jogo.num_jogadores
            # In original game, jogador_atual advanced after executar_acao, so the player who applied was jogador_idx
            # Get scores
            original_score = jogo.estado.tabuleiros[jogador_idx].pontuacao
            sim_score = sim.estado.tabuleiros[jogador_idx].pontuacao
            val = sim_score - original_score
            # heurística adicional: se a ação deixou linha padrão mais próxima de completar, dar pequeno bônus
            # contagem de peças na linha escolhida (se não chão)
            if ac.linha >= 0:
                tab = jogo.estado.tabuleiros[jogador_idx]
                filled_before = len(tab.linhas_padrao.linhas[ac.linha])
                val += 0.1 * min( (ac.linha+1) - filled_before, 1)
            # desempate aleatório
            if val > best_val:
                best_val = val
                best_actions = [ac]
            elif val == best_val:
                best_actions.append(ac)

        if self.pref_random and len(best_actions) > 1:
            return random.choice(best_actions)
        return best_actions[0]

# ----------------------------
# Minimax AI (profundidade limitada)
# ----------------------------
class MinimaxAI:
    """
    Minimax para Azul:
    - Projetado principalmente para 2 jogadores (zero-sum)
    - Para >2 jogadores, jogadores não-alvo são simulados com política gulosa (approx).
    - Depth: profundidade de plies (cada ply = uma ação de um jogador).
    - Heurística de avaliação: diferença de pontuação (target - others), além de proximidade de completar linhas.
    """

    def __init__(self, depth=3, preferencia_empate_random=True):
        self.depth = depth
        self.pref_random = preferencia_empate_random

    def escolher_acao(self, jogo: JogoAzul) -> Optional[Acao]:
        acoes = jogo.obter_acoes_legais()
        if not acoes:
            return None
        player_idx = jogo.estado.jogador_atual

        def eval_state(sim: JogoAzul, target_idx: int):
            # avaliação heurística do estado: diferença de pontuação + proximidade
            target_score = sim.estado.tabuleiros[target_idx].pontuacao
            others_score = sum(t.pontuacao for i,t in enumerate(sim.estado.tabuleiros) if i != target_idx)
            val = float(target_score) - float(others_score)/(max(1, sim.num_jogadores-1))
            # proximidade de completar linhas: +0.2 por linha parcialmente preenchida
            tab = sim.estado.tabuleiros[target_idx]
            for r in range(5):
                cnt = sum(1 for c in range(5) if tab.parede.celulas[r][c] is not None)
                if cnt > 0:
                    val += 0.05 * cnt
            return val

        def minimax(sim: JogoAzul, depth, maximizing_idx):
            if sim.estado.jogo_terminou or depth == 0:
                return eval_state(sim, player_idx)
            cur = sim.estado.jogador_atual
            acoes_local = sim.obter_acoes_legais()
            if not acoes_local:
                # passar turno
                sim2 = copy.deepcopy(sim)
                sim2.estado.jogador_atual = (sim2.estado.jogador_atual + 1) % sim2.num_jogadores
                return minimax(sim2, depth-1, maximizing_idx)
            if cur == player_idx:
                # maximizing
                best = -1e9
                for ac in acoes_local:
                    sim2 = copy.deepcopy(sim)
                    sim2.executar_acao(copy.deepcopy(ac))
                    v = minimax(sim2, depth-1, maximizing_idx)
                    if v > best:
                        best = v
                return best
            else:
                # opponent: minimize (if >2 players use greedy policy for them)
                if sim.num_jogadores == 2:
                    best = 1e9
                    for ac in acoes_local:
                        sim2 = copy.deepcopy(sim)
                        sim2.executar_acao(copy.deepcopy(ac))
                        v = minimax(sim2, depth-1, maximizing_idx)
                        if v < best:
                            best = v
                    return best
                else:
                    # approximate opponent with greedy choice (fast)
                    # pick greedy action for opponent
                    best = 1e9
                    for ac in acoes_local:
                        sim2 = copy.deepcopy(sim)
                        sim2.executar_acao(copy.deepcopy(ac))
                        v = minimax(sim2, depth-1, maximizing_idx)
                        if v < best:
                            best = v
                    return best

        # choose best action by evaluating minimax value after applying action
        best_val = -1e9
        best_actions = []
        for ac in acoes:
            sim = copy.deepcopy(jogo)
            sim.executar_acao(copy.deepcopy(ac))
            v = minimax(sim, self.depth-1, player_idx)
            if v > best_val:
                best_val = v
                best_actions = [ac]
            elif v == best_val:
                best_actions.append(ac)

        if self.pref_random and len(best_actions) > 1:
            return random.choice(best_actions)
        return best_actions[0]

# ----------------------------
# MCTS AI (Monte Carlo Tree Search)
# ----------------------------
class MCTS_AI:
    """
    Monte Carlo Tree Search with UCT.
    - iters: number of simulations
    - rollout_policy: "random" or "greedy"
    - reward: final score difference (root_player_score - avg(other_scores))
    """

    class Node:
        def __init__(self, state: JogoAzul, parent=None, action_from_parent: Optional[Acao]=None):
            self.state = state  # a deep-copied state for this node
            self.parent = parent
            self.action_from_parent = action_from_parent
            self.children = {}  # action -> Node
            self.visits = 0
            self.value = 0.0
            self.untried_actions = state.obter_acoes_legais()

    def __init__(self, iters=800, cpuct=1.4, rollout_policy="random"):
        self.iters = iters
        self.cpuct = cpuct
        assert rollout_policy in ("random", "greedy")
        self.rollout_policy = rollout_policy

    def escolher_acao(self, jogo: JogoAzul) -> Optional[Acao]:
        acoes = jogo.obter_acoes_legais()
        if not acoes:
            return None
        root = self.Node(copy.deepcopy(jogo))

        root_player_idx = jogo.estado.jogador_atual

        for _ in range(self.iters):
            node = root
            # 1) Selection
            while node.untried_actions == [] and node.children:
                node = self._uct_select(node)
            # 2) Expansion
            if node.untried_actions:
                ac = random.choice(node.untried_actions)
                # remove ac from untried actions
                node.untried_actions.remove(ac)
                new_state = copy.deepcopy(node.state)
                new_state.executar_acao(copy.deepcopy(ac))
                child = self.Node(new_state, parent=node, action_from_parent=ac)
                node.children[self._acao_key(ac)] = child
                node = child
            # 3) Simulation (rollout)
            reward = self._rollout(node.state, root_player_idx)
            # 4) Backpropagation
            self._backprop(node, reward)

        # choose the child with highest visits (robust)
        best_child = None
        best_visits = -1
        for c in root.children.values():
            if c.visits > best_visits:
                best_visits = c.visits
                best_child = c
        # if no children (no expansion happened), fallback to random legal action
        if best_child is None:
            return random.choice(acoes)
        return best_child.action_from_parent

    def _acao_key(self, ac: Acao):
        # turn action into tuple key; Acao is dataclass with simple fields so tuple works
        fonte = ac.fonte
        return (fonte[0], fonte[1], ac.cor, ac.linha)

    def _uct_select(self, node: "MCTS_AI.Node"):
        # choose child maximizing UCT = Q/N + c * sqrt(ln(N_parent)/N_child)
        total_visits = sum(c.visits for c in node.children.values()) or 1
        best_score = -1e9
        best_child = None
        for child in node.children.values():
            if child.visits == 0:
                uct = 1e9 + random.random()
            else:
                exploitation = child.value / child.visits
                exploration = math.sqrt(math.log(total_visits) / child.visits)
                uct = exploitation + self.cpuct * exploration
            if uct > best_score:
                best_score = uct
                best_child = child
        return best_child

    def _rollout(self, state: JogoAzul, root_player_idx: int):
        sim = copy.deepcopy(state)
        # play until terminal or until rollout depth (to avoid infinite)
        rollout_depth_limit = 100  # generous cap
        steps = 0
        while not sim.estado.jogo_terminou and steps < rollout_depth_limit:
            acoes = sim.obter_acoes_legais()
            if not acoes:
                # advance if no actions (shouldn't happen often)
                sim.estado.jogador_atual = (sim.estado.jogador_atual + 1) % sim.num_jogadores
                steps += 1
                continue
            if self.rollout_policy == "random":
                ac = random.choice(acoes)
            else:
                # greedy rollout: use simple immediate-evaluation greedy
                best_v = -1e9
                best_a = None
                for candidate in acoes:
                    s = copy.deepcopy(sim)
                    s.executar_acao(copy.deepcopy(candidate))
                    # evaluate immediate score change for the player who just moved
                    mover_idx = (sim.estado.jogador_atual) % sim.num_jogadores
                    val = s.estado.tabuleiros[mover_idx].pontuacao - sim.estado.tabuleiros[mover_idx].pontuacao
                    if val > best_v:
                        best_v = val
                        best_a = candidate
                ac = best_a or random.choice(acoes)
            sim.executar_acao(copy.deepcopy(ac))
            steps += 1
        # reward: final score difference for root player
        root_score = sim.estado.tabuleiros[root_player_idx].pontuacao
        other_scores = sum(sim.estado.tabuleiros[i].pontuacao for i in range(sim.num_jogadores) if i != root_player_idx)
        # average others
        if sim.num_jogadores > 1:
            reward = float(root_score) - float(other_scores) / (sim.num_jogadores - 1)
        else:
            reward = float(root_score)
        return reward

    def _backprop(self, node: "MCTS_AI.Node", reward: float):
        cur = node
        while cur is not None:
            cur.visits += 1
            cur.value += reward
            cur = cur.parent

# ----------------------------
# Usage helper: factory function
# ----------------------------
def get_ai(nome: str, **kwargs):
    nome = nome.lower()
    if nome in ("greedy", "gulosa"):
        return GreedyAI(**kwargs)
    if nome in ("minimax", "mini"):
        return MinimaxAI(**kwargs)
    if nome in ("mcts", "montecarlo", "uct"):
        return MCTS_AI(**kwargs)
    raise ValueError("AI desconhecida: " + nome)
