# interface_terminal.py
# Funções de visualização para o jogo Azul no terminal usando blocos ANSI.

import os
from azulejos import CorAzulejo

RESET = "\033[0m"
# colors: background blocks with two spaces
COLORS_BLOCK = {
    CorAzulejo.AZUL:    "\033[44m  \033[0m",
    CorAzulejo.AMARELO: "\033[43m  \033[0m",
    CorAzulejo.VERMELHO:"\033[41m  \033[0m",
    CorAzulejo.PRETO:   "\033[40m  \033[0m",
    CorAzulejo.BRANCO:  "\033[47m  \033[0m",
    None:               " ."
}

def tile_block(az):
    if az is None:
        return COLORS_BLOCK[None]
    return COLORS_BLOCK.get(az, " ?")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_factories(expositores):
    """
    Expositores: lista de Expositor
    Cada expositor tem .azulejos (lista de CorAzulejo)
    Mostra até 8 expositores em disposição radial.
    """
    # Convert each expositor's tiles to list of values for easy rendering
    tiles_list = []
    for e in expositores:
        tiles = [t for t in e.azulejos]
        # pad to 4
        while len(tiles) < 4:
            tiles.append(None)
        tiles_list.append(tiles)

    # Ensure length 8 for layout (pad with empty)
    while len(tiles_list) < 8:
        tiles_list.append([None,None,None,None])

    # layout 7 rows x 3 columns positions as in previous design
    mapping = {
        1: (0,0),
        2: (0,1),
        3: (0,2),
        4: (2,2),
        5: (4,2),
        6: (4,1),
        7: (4,0),
        8: (2,0),
    }
    grid = [[None for _ in range(3)] for _ in range(5)]
    for idx in range(8):
        pos = mapping[idx+1]
        grid[pos[0]][pos[1]] = tiles_list[idx]

    print("============== EXPOSITORES ==============")
    # Print row by row with boxes
    for r in range(5):
        # top border
        line = ""
        for c in range(3):
            if grid[r][c] is None:
                line += " " * 14
            else:
                line += "  ┌───────┐  "
        print(line)
        # tiles row 1
        line = ""
        for c in range(3):
            if grid[r][c] is None:
                line += " " * 14
            else:
                t = grid[r][c]
                line += "  │ " + tile_block(t[0]) + " " + tile_block(t[1]) + " │  "
        print(line)
        # tiles row 2
        line = ""
        for c in range(3):
            if grid[r][c] is None:
                line += " " * 14
            else:
                t = grid[r][c]
                line += "  │ " + tile_block(t[2]) + " " + tile_block(t[3]) + " │  "
        print(line)
        # bottom border
        line = ""
        for c in range(3):
            if grid[r][c] is None:
                line += " " * 14
            else:
                line += "  └───────┘  "
        print(line)
    print("=========================================\n")

def show_center(centro):
    print("========== CENTRO DA MESA ==========")
    if centro.token_primeiro:
        print("[Token Primeiro] ", end="")
    if centro.azulejos:
        for a in centro.azulejos:
            print(tile_block(a), end=" ")
    else:
        print("(vazio)", end="")
    print("\n====================================\n")

def show_board_do_jogador(tabuleiro, nome):
    print(f"--- Tabuleiro: {nome} ---")
    # linhas padrão
    print("Linhas padrão (1..5):")
    for i, linha in enumerate(tabuleiro.linhas):
        cap = tabuleiro.capacidade_linha(i)
        content = "".join(tile_block(a) for a in linha)
        pad = "  " * (cap - len(linha))
        print(f" {i+1} [{len(linha)}/{cap}]: {content}{pad}")
    # piso
    print("Piso: ", end="")
    if tabuleiro.piso:
        for a in tabuleiro.piso:
            if a == "TOKEN":
                print("\033[1m(FIRST)\033[0m", end=" ")
            else:
                print(tile_block(a), end=" ")
    else:
        print("(vazio)", end="")
    print("\nParede:")
    # parede 5x5
    header = "     1  2  3  4  5"
    print(header)
    print("   ┌───────────────┐")
    for r in range(5):
        line = f" {r+1} │ "
        for c in range(5):
            line += tile_block(tabuleiro.parede[r][c]) + " "
        line += "│"
        print(line)
    print("   └───────────────┘\n")

def show_scores(jogadores):
    print("========== PLACAR ==========")
    for j in jogadores:
        print(f"{j.nome:15s} : {j.pontos:3d}")
    print("============================\n")

def show_full_state(estado, jogador_atual=None):
    """
    Exibe expositores, centro, placar e o tabuleiro do jogador atual (se fornecido).
    estado é o mesmo dict passado entre módulos.
    """
    clear_screen()
    show_factories(estado["expositores"])
    show_center(estado["centro"])
    show_scores(estado["jogadores"])
    if jogador_atual:
        show_board_do_jogador(jogador_atual.tabuleiro, jogador_atual.nome)
