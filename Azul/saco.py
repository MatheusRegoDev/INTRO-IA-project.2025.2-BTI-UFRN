# saco.py
import random
from azuleijos import gerar_todos_azulejos

class Saco:
    def __init__(self):
        self.azulejos = gerar_todos_azulejos()
        self.descarte = []

    def embaralhar(self):
        random.shuffle(self.azulejos)

    def puxar(self, n):
        """
        Puxa até n azulejos do saco. Reabastece do descarte se necessário.
        Retorna lista de azulejos (pode ser menos se não houver mais peças).
        """
        resultado = []
        while len(resultado) < n:
            if not self.azulejos:
                # Repor do descarte
                self.azulejos = self.descarte
                self.descarte = []
                random.shuffle(self.azulejos)
                if not self.azulejos:
                    break
            pegar = min(n - len(resultado), len(self.azulejos))
            resultado += self.azulejos[:pegar]
            self.azulejos = self.azulejos[pegar:]
        return resultado

    def descartar(self, azulejos):
        self.descarte += azulejos
