# expositores.py
class Expositor:
    def __init__(self, id_):
        self.id = id_
        self.azulejos = []

    def preencher(self, saco):
        self.azulejos = saco.puxar(4)

    def vazio(self):
        return len(self.azulejos) == 0

    def retirar_cor(self, cor):
        """
        Remove todos os azulejos da cor escolhida e retorna (escolhidos, resto).
        Expositor fica vazio após a retirada.
        """
        escolhidos = [a for a in self.azulejos if a == cor]
        resto = [a for a in self.azulejos if a != cor]
        self.azulejos = []
        return escolhidos, resto

    def cores_disponiveis(self):
        return sorted(set(self.azulejos), key=lambda x: x.value)

    def __str__(self):
        if self.vazio():
            return f"Expositor {self.id}: (vazio)"
        counts = {}
        for a in self.azulejos:
            counts[a] = counts.get(a, 0) + 1
        s = ", ".join(f"{c.name}:{counts[c]}" for c in sorted(counts, key=lambda x: x.name))
        return f"Expositor {self.id}: {s}"
