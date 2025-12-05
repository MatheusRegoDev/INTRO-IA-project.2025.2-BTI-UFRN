# jogo.py
from expositores import Expositor
from centro import CentroMesa
from saco import Saco
from jogador import Jogador
from azuleijos import ALL_COLORS
import interface as view

class Jogo:
    def __init__(self, jogadores):
        """
        jogadores: lista de Jogador (instâncias já criadas)
        """
        self.jogadores = jogadores
        self.saco = Saco()
        self.centro = CentroMesa()
        self.expositores = []
        self.num_expositores = 5 if len(self.jogadores) == 2 else 7
        self.rodada = 0
        self.all_colors = ALL_COLORS
        # quem tem token primeiro (index); None até token ser pego (we'll store owner after first token pick)
        self.owner_first_token = None

    def preparar_rodada(self):
        self.rodada += 1
        self.centro = CentroMesa()
        self.expositores = [Expositor(i+1) for i in range(self.num_expositores)]
        for e in self.expositores:
            e.preencher(self.saco)

    def _todas_fontes_vazias(self):
        ex_vazios = all(e.vazio() for e in self.expositores)
        centro_vazio = (not self.centro.azulejos) and (not self.centro.token_primeiro)
        return ex_vazios and centro_vazio

    def _aplicar_escolha(self, jogador, escolha):
        fonte = escolha["fonte"]
        cor = escolha["cor"]
        linha = escolha["linha"]
        escolhidos = []
        took_token = False

        if fonte[0] == "expositor":
            idx = fonte[1]
            escolhidos, resto = self.expositores[idx].retirar_cor(cor)
            # restos vão para o centro
            if resto:
                self.centro.adicionar(resto)
        else:
            escolhidos, took_token = self.centro.retirar_cor(cor)
            if took_token:
                # marca que este jogador pegou o token (owner_first_token)
                if self.owner_first_token is None:
                    self.owner_first_token = jogador

        # aplicar azulejos ao tabuleiro
        if linha == -1:
            jogador.tabuleiro.piso += escolhidos
        else:
            jogador.tabuleiro.adicionar_a_linha(linha, escolhidos, to_floor_if_excess=True)

        # se tomou o token, adicionar marcador no piso
        if took_token:
            jogador.tabuleiro.piso.append("TOKEN")

    def fase_coleta(self):
        # ordem de jogo: começa pelo jogador que tem o token (owner_first_token) se definido,
        # caso contrário começa no jogador 0
        # durante a rodada, a ordem é circular a partir do primeiro jogador.
        start_idx = 0
        if self.owner_first_token is not None:
            try:
                start_idx = self.jogadores.index(self.owner_first_token)
            except ValueError:
                start_idx = 0

        turno_offset = 0
        while not self._todas_fontes_vazias():
            jogador = self.jogadores[(start_idx + turno_offset) % len(self.jogadores)]
            estado = {
                "expositores": self.expositores,
                "centro": self.centro,
                "jogadores": self.jogadores,
                "indice_jogador": (start_idx + turno_offset) % len(self.jogadores),
                "all_colors": self.all_colors
            }
            escolha = jogador.escolher_jogada(estado)
            if escolha is None:
                # nenhuma jogada possível (salto)
                turno_offset += 1
                continue
            self._aplicar_escolha(jogador, escolha)
            turno_offset += 1

    def fase_parede_e_pontuacao(self):
        for jogador in self.jogadores:
            pontos_ganhos, to_discard = jogador.tabuleiro.finalizar_rodada()
            jogador.pontos += pontos_ganhos
            if to_discard:
                self.saco.descartar(to_discard)
        # após fase de pontuação, resetamos owner_first_token (o token ficará no centro para próxima rodada)
        self.owner_first_token = None

    def jogo_terminou(self):
        for jogador in self.jogadores:
            for r in range(5):
                if all(jogador.tabuleiro.parede[r][c] is not None for c in range(5)):
                    return True
        return False

    def aplicar_bonificacoes_finais(self):
        for jogador in self.jogadores:
            bonus = jogador.tabuleiro.pontuacao_final_bonificacoes()
            jogador.pontos += bonus

    def jogar(self):
        # loop principal
        while True:
            self.preparar_rodada()
            # exibir estado inicial da rodada
            estado = {"expositores": self.expositores, "centro": self.centro, "jogadores": self.jogadores, "all_colors": self.all_colors}
            view.show_full_state(estado)
            input("Pressione Enter para começar a fase de coleta...")

            self.fase_coleta()
            # após coleta, fase de parede e pontuação
            self.fase_parede_e_pontuacao()
            # exibir placar
            estado = {"expositores": self.expositores, "centro": self.centro, "jogadores": self.jogadores, "all_colors": self.all_colors}
            view.show_full_state(estado)
            print(f"=== Pontuação após rodada {self.rodada} ===")
            for j in self.jogadores:
                print(f"{j.nome}: {j.pontos}")
            input("Pressione Enter para próxima rodada...")

            if self.jogo_terminou():
                break

        # fim de jogo
        self.aplicar_bonificacoes_finais()
        view.clear_screen()
        print("=== JOGO FINALIZADO ===")
        view.show_scores(self.jogadores)
        ranking = sorted(self.jogadores, key=lambda x: x.pontos, reverse=True)
        print(f"Vencedor: {ranking[0].nome} com {ranking[0].pontos} pontos")
