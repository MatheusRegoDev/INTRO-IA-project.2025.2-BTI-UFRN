from enum import Enum
import random

class CorAzulejo(Enum):
    AZUL = "B"     # Blue
    AMARELO = "Y"  # Yellow
    VERMELHO = "R" # Red
    PRETO = "K"    # Black
    BRANCO = "W"   # White

    def __str__(self):
        return self.value

ALL_COLORS = list(CorAzulejo)

def gerar_todos_azulejos():
    """
    Gera 20 azulejos de cada cor (100 total), embaralhados.
    """
    azulejos = []
    for cor in ALL_COLORS:
        azulejos += [cor] * 20
    random.shuffle(azulejos)
    return azulejos
