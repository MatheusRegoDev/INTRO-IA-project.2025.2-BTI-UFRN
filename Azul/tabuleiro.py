# tabuleiro.py
from azuleijos import CorAzulejo

FLOOR_PENALTIES = [-1, -1, -2, -2, -2, -3, -3]  # penalidades do piso (máx 7 posições)

# WALL_TEMPLATE define qual cor "cabe" em cada posição da parede por linha
# (padrão clássico do Azul)
W = CorAzulejo.BRANCO
B = CorAzulejo.AZUL
R = CorAzulejo.VERMELHO
K = CorAzulejo.PRETO
Y = CorAzulejo.AMARELO

WALL_TEMPLATE = [
    [B, Y, R, K, W],
    [W, B, Y, R, K],
    [K, W, B, Y, R],
    [R, K, W, B, Y],
    [Y, R, K, W, B],
]

class Tabuleiro:
    def __init__(self):
        # linhas de padrão: índices 0..4 com capacidades 1..5
        self.linhas = [[] for _ in range(5)]
        # parede 5x5 (None ou CorAzulejo)
        self.parede = [[None]*5 for _ in range(5)]
        # piso: lista de azulejos (ou marcador "TOKEN")
        self.piso = []

    def capacidade_linha(self, idx):
        return idx + 1

    def pode_colocar_na_linha(self, linha_idx, cor):
        linha = self.linhas[linha_idx]
        # se linha já tem cor diferente -> não pode
        if len(linha) > 0 and any(a != cor for a in linha):
            return False
        # se cor já presente na mesma linha na parede -> não pode
        for c in range(5):
            if self.parede[linha_idx][c] == cor:
                return False
        # se linha já cheia -> não pode
        return len(linha) < self.capacidade_linha(linha_idx)

    def adicionar_a_linha(self, linha_idx, azulejos, to_floor_if_excess=True):
        """
        Adiciona azulejos à linha padrão; excesso vai para o piso.
        Retorna lista de azulejos que foram para o piso.
        """
        capacidade = self.capacidade_linha(linha_idx)
        linha = self.linhas[linha_idx]
        espaço = capacidade - len(linha)
        if espaço >= len(azulejos):
            self.linhas[linha_idx] += azulejos
            return []
        else:
            para_linha = azulejos[:espaço]
            excesso = azulejos[espaço:]
            self.linhas[linha_idx] += para_linha
            if to_floor_if_excess:
                self.piso += excesso
            return excesso

    def finalizar_rodada(self):
        """
        Move linhas completas para a parede e calcula pontos.
        Retorna (pontos_ganhos, azulejos_para_descarte).
        """
        pontos = 0
        para_descarte = []
        for i in range(5):
            capacidade = self.capacidade_linha(i)
            if len(self.linhas[i]) == capacidade:
                cor = self.linhas[i][0]
                # achar coluna alvo na parede via WALL_TEMPLATE
                target_col = None
                for col in range(5):
                    if WALL_TEMPLATE[i][col] == cor:
                        target_col = col
                        break
                if target_col is None:
                    # fallback: primeiro livre
                    for col in range(5):
                        if self.parede[i][col] is None:
                            target_col = col
                            break
                # colocar um azulejo na parede
                self.parede[i][target_col] = cor
                # o restante (capacidade - 1) vão para descarte
                descarte = self.linhas[i][1:]
                para_descarte += descarte
                self.linhas[i] = []
                # calcular pontos pela colocação
                ganhos = self._calcular_pontos_posicao(i, target_col)
                pontos += ganhos
            else:
                # linhas incompletas permanecem
                pass

        # penalidades do piso
        penalty = 0
        for idx, az in enumerate(self.piso[:len(FLOOR_PENALTIES)]):
            penalty += FLOOR_PENALTIES[idx]
            # todo azulejo no piso vai para descarte (exceto token que é marcador)
            if az != "TOKEN":
                para_descarte.append(az)
        # limpar piso (token removido)
        self.piso = []
        return pontos + penalty, para_descarte

    def _calcular_pontos_posicao(self, row, col):
        base = 1
        horiz = 0
        # esquerda
        c = col - 1
        while c >= 0 and self.parede[row][c] is not None:
            horiz += 1
            c -= 1
        # direita
        c = col + 1
        while c < 5 and self.parede[row][c] is not None:
            horiz += 1
            c += 1

        vert = 0
        r = row - 1
        while r >= 0 and self.parede[r][col] is not None:
            vert += 1
            r -= 1
        r = row + 1
        while r < 5 and self.parede[r][col] is not None:
            vert += 1
            r += 1

        if horiz == 0 and vert == 0:
            return base
        else:
            return base + horiz + vert

    def pontuacao_final_bonificacoes(self):
        bonus = 0
        # linhas completas
        for r in range(5):
            if all(self.parede[r][c] is not None for c in range(5)):
                bonus += 2
        # colunas completas
        for c in range(5):
            if all(self.parede[r][c] is not None for r in range(5)):
                bonus += 7
        # cores completas
        for cor in [CorAzulejo.AZUL, CorAzulejo.AMARELO, CorAzulejo.VERMELHO, CorAzulejo.PRETO, CorAzulejo.BRANCO]:
            cnt = sum(1 for r in range(5) for cc in range(5) if self.parede[r][cc] == cor)
            if cnt == 5:
                bonus += 10
        return bonus

    def __str__(self):
        s = "Linhas padrão:\n"
        for i, l in enumerate(self.linhas):
            s += f" {i+1} [{len(l)}/{self.capacidade_linha(i)}]: " + " ".join(str(x.value) for x in l) + "\n"
        s += "Piso: " + " ".join(str(x) for x in self.piso) + "\n"
        s += "Parede:\n"
        for r in range(5):
            s += " ".join(self.parede[r][c].value if self.parede[r][c] else "." for c in range(5)) + "\n"
        return s
