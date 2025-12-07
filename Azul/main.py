# main.py
from jogador import Jogador
from jogo import Jogo
from ai_agents import GreedyAgent, MinimaxAgent, MCTSAgent

def escolher_tipo_agente():
    print("\nEscolha o Agente de IA:")
    print(" 1. CPU Padrão (Heurística simples/rápida)")
    print(" 2. GreedyAgent (Simulação de rodada, mais lento)")
    print(" 3. MinimaxAgent (Poda Alpha-Beta, muito mais lento)")
    print(" 4. MCTSAgent (Monte Carlo Tree Search, lento)")
    while True:
        escolha = input("Opção (1-4): ").strip()
        if escolha == '1':
            return "cpu_padrao"
        elif escolha == '2':
            return "greedy"
        elif escolha == '3':
            return "minimax"
        elif escolha == '4':
            return "mcts"
        else:
            print("Opção inválida.")

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
            # Se for CPU, permite escolher o tipo de Agente
            agente_tipo = escolher_tipo_agente()
            nome_base = f"CPU {i+1}"
            
            if agente_tipo == "cpu_padrao":
                # Usa a classe padrão Jogador com tipo="cpu" (heurística simples)
                jogadores.append(Jogador(nome_base, tipo="cpu"))
            elif agente_tipo == "greedy":
                # Usa o GreedyAgent com 12 simulações (parâmetros podem ser ajustados)
                jogadores.append(GreedyAgent(f"Greedy {i+1}", sim_per_option=12))
            elif agente_tipo == "minimax":
                # Usa o MinimaxAgent com profundidade 2 (parâmetros podem ser ajustados)
                jogadores.append(MinimaxAgent(f"Minimax {i+1}", depth=2))
            elif agente_tipo == "mcts":
                # Usa o MCTSAgent com 200 iterações (parâmetros podem ser ajustados)
                jogadores.append(MCTSAgent(f"MCTS {i+1}", iterations=200))
                
        else:
            # Jogador humano
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