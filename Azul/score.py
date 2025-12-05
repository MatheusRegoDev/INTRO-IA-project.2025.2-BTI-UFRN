# score.py
# (Hoje a lógica de pontuação está embutida em tabuleiro.finalizar_rodada e em Tabuleiro._calcular_pontos_posicao)
# Este módulo fica disponível caso queira regras/ajustes futuros. Mantido simples.

def aplicar_penalidades(pontos, penalty):
    return pontos + penalty
