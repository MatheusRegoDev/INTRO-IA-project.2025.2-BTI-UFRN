from saco import SacoAzuleijos

class ExpositorFabrica:
    def __init__(self, saco:SacoAzuleijos, n_azuleijos_expositores=4):
        self.azuleijos = bag.draw(n_azuleijos_expositores)

    def pegar_cor(self, cor):
        cor_escolhido = [t for t in self.azuleijos if t == cor]
        resto = [t for t in self.azuleijos if t != cor]
        self.azuleijos = []
        return cor_escolhido, resto
    
    def is_vazio(self):
        return(self.azuleijos) == 0
    