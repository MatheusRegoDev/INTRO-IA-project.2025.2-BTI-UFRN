from azuleijos import ALL_COLORS
import random

class SacoAzuleijos:
    def __init__(self):
        ''' Gera os vintes azuleijos de cada cor de forma aleatória'''
        self.azuleijos = []
        for cor in ALL_COLORS:
            self.azuleijos.extend([cor] * 20)
        random.shuffle(self.azuleijos)
        self.pilha_descarte = []

    def sacar_azuleijos(self, n_azuleijos):
        if len(self.azuleijos) < n_azuleijos:
            self.refil = ()
        saque_azuleijos = [self.azuleijos.pop() for _ in range(n_azuleijos)]
        return saque_azuleijos
    
    def refil(self):
        if self.pilha_descarte:
            self.azuleijos = self.pilha_descarte[:]
            random.shuffle(self.azuleijos)
            self.pilha_descarte = []