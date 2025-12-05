# main.py
from jogador import Jogador
from jogo import Jogo

def escolher_jogadores():
    print("Bem-vindo ao Azul (CLI)!")
    while True:
        try:
            n = int(input("Número de jogadores (2-4): ").strip())
            if 2 <= n <= 4:
                break
            else:
                print("Escolha entre 2 e 4 jogadores.")
        except:
            print("Entrada inválida.")
    jogadores = []
    for i in range(n):
        tipo = input(f"Jogador {i+1}: humano ou cpu? (h/c): ").strip().lower()
        if tipo == "c":
            jogadores.append(Jogador(f"CPU {i+1}", tipo="cpu"))
        else:
            nome = input(f"Nome do jogador {i+1}: ").strip()
            if not nome:
                nome = f"Jogador {i+1}"
            jogadores.append(Jogador(nome, tipo="human"))
    return jogadores

def main():
    jogadores = escolher_jogadores()
    jogo = Jogo(jogadores)
    jogo.jogar()

if __name__ == "__main__":
    main()
