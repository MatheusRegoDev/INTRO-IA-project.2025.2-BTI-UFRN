# centro_da_mesa.py
class CentroMesa:
    def __init__(self):
        self.azulejos = []
        self.token_primeiro = True  # token do primeiro jogador disponível no início

    def adicionar(self, itens):
        self.azulejos += itens

    def vazio(self):
        return len(self.azulejos) == 0 and not self.token_primeiro

    def retirar_cor(self, cor):
        """
        Retira todos azulejos da cor escolhida do centro e retorna (selecionados, took_token)
        took_token = True se o jogador pegar o token primeiro (se token estava presente).
        """
        selecionados = [a for a in self.azulejos if a == cor]
        self.azulejos = [a for a in self.azulejos if a != cor]
        took_token = False
        if self.token_primeiro:
            # ao retirar do centro, o jogador pega o token (se ainda estava lá)
            self.token_primeiro = False
            took_token = True
        return selecionados, took_token

    def cores_disponiveis(self):
        return sorted(set(self.azulejos), key=lambda x: x.value)

    def __str__(self):
        s = ""
        if self.token_primeiro:
            s += "[Token Primeiro] "
        if self.azulejos:
            counts = {}
            for a in self.azulejos:
                counts[a] = counts.get(a, 0) + 1
            s += ", ".join(f"{c.name}:{counts[c]}" for c in sorted(counts, key=lambda x: x.name))
        else:
            s += "(vazio)"
        return f"Centro: {s}"
