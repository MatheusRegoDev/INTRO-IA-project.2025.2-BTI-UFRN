# jogador.py
from tabuleiro import Tabuleiro
import random
from azulejos import CorAzulejo
import interface as view  # para renderizar assistência ao jogador (entrada/mostra)

class Jogador:
    def __init__(self, nome, tipo="human"):
        self.nome = nome
        self.tabuleiro = Tabuleiro()
        self.pontos = 0
        self.tipo = tipo  # "human" ou "cpu"

    def escolher_jogada(self, estado):
        """
        estado: dict com {expositores, centro, jogadores, indice_jogador, all_colors}
        Retorna: {"fonte": ("expositor", idx) or ("centro", None), "cor": CorAzulejo, "linha": 0..4 or -1 for piso}
        """
        if self.tipo == "cpu":
            return self._escolha_cpu(estado)
        else:
            return self._escolha_humana(estado)

    def _escolha_cpu(self, estado):
        # Heurística simples:
        # 1) tentar completar uma linha (se houver cor que ajude)
        # 2) senão, pegar maior quantidade disponível
        opções = []
        # coletar opções de expositores
        for i, e in enumerate(estado["expositores"]):
            if not e.vazio():
                cores = e.cores_disponiveis()
                for cor in cores:
                    escolhidos = [a for a in e.azulejos if a == cor]
                    opções.append(("expositor", i, cor, len(escolhidos)))
        # centro
        centro = estado["centro"]
        if centro.azulejos or centro.token_primeiro:
            cores = centro.cores_disponiveis()
            for cor in cores:
                cnt = sum(1 for a in centro.azulejos if a == cor)
                opções.append(("centro", None, cor, cnt))
        # escolher melhor por quantidade
        if not opções:
            return None
        opções.sort(key=lambda x: (-x[3], x[2].value))
        fonte_tipo, idx, cor, cnt = opções[0]
        # escolher linha que aceite a cor preferencialmente que esteja parcialmente preenchida
        linhas_validas = [i for i in range(5) if self.tabuleiro.pode_colocar_na_linha(i, cor)]
        # priorizar linha que já tenha peças (para completar)
        linhas_com_pecas = [i for i in linhas_validas if len(self.tabuleiro.linhas[i])>0]
        if linhas_com_pecas:
            linha = max(linhas_com_pecas, key=lambda x: len(self.tabuleiro.linhas[x]))
        elif linhas_validas:
            linha = min(linhas_validas)  # escolher a menor linha disponível
        else:
            linha = -1
        return {"fonte": (fonte_tipo, idx), "cor": cor, "linha": linha}

    def _escolha_humana(self, estado):
        # mostra visão com a interface
        view.clear_screen()
        view.show_full_state(estado, jogador_atual=self)
        # solicitar escolha de fonte
        while True:
            raw = input("Escolha fonte (expositor N) ou (centro): ").strip().lower()
            if raw.startswith("expositor"):
                parts = raw.split()
                if len(parts) == 2 and parts[1].isdigit():
                    idx = int(parts[1]) - 1
                    if 0 <= idx < len(estado["expositores"]) and not estado["expositores"][idx].vazio():
                        fonte = ("expositor", idx)
                        break
                print("Expositor inválido.")
            elif raw in ("centro", "c"):
                if estado["centro"].azulejos or estado["centro"].token_primeiro:
                    fonte = ("centro", None)
                    break
                print("Centro vazio.")
            else:
                print("Entrada inválida. Ex.: 'expositor 1' ou 'centro'")

        # escolher cor disponível na fonte
        cores_disponiveis = []
        if fonte[0] == "expositor":
            cores_disponiveis = estado["expositores"][fonte[1]].cores_disponiveis()
        else:
            cores_disponiveis = estado["centro"].cores_disponiveis()
        if not cores_disponiveis:
            print("Nenhuma cor disponível nessa fonte (erro).")
            return None

        print("Cores disponíveis:", ", ".join(c.name for c in cores_disponiveis))
        while True:
            escolha_cor = input("Escolha a cor (nome: AZUL, AMARELO, VERMELHO, PRETO, BRANCO): ").strip().upper()
            try:
                cor = CorAzulejo[escolha_cor]
                if cor in cores_disponiveis:
                    break
                else:
                    print("Cor não disponível na fonte.")
            except Exception:
                print("Nome de cor inválido.")

        # escolher linha
        print("Seu tabuleiro atual:")
        print(self.tabuleiro)
        while True:
            escolha_linha = input("Escolha linha (1-5) para padrão, ou 0 para enviar ao piso: ").strip()
            if escolha_linha.isdigit():
                ln = int(escolha_linha)
                if ln == 0:
                    linha = -1
                    break
                if 1 <= ln <= 5:
                    if self.tabuleiro.pode_colocar_na_linha(ln-1, cor):
                        linha = ln-1
                        break
                    else:
                        print("Não é possível colocar nessa linha (conflito).")
                else:
                    print("Linha inválida.")
            else:
                print("Entrada inválida.")
        return {"fonte": fonte, "cor": cor, "linha": linha}

    def __str__(self):
        return f"{self.nome} ({'CPU' if self.tipo=='cpu' else 'HUM'}) - Pontos: {self.pontos}"
