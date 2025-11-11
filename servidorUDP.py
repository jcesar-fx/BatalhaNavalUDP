import socket
import json

HOST = '127.0.0.1'
PORT = 12345

# lista de jogadores conectados
listaJogadores = []

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    print(f"Servidor UDP escutando em {HOST}:{PORT}...")

    while True:
        data, endereco = s.recvfrom(1024)
        
        # realiza a conexão de novos jogadores
        # se o endereço do jogador não está na lista de jogadores, adiciona ele na lista

        if endereco not in listaJogadores:
            if len(listaJogadores) < 2:
                listaJogadores.append(endereco)
                print(f"Jogador conectado: {endereco}. Total de jogadores: {len(listaJogadores)}")
                
                # notifica ao jogador que ele foi conectado
                s.sendto(json.dumps({"type": "connected", "numero_jogador": len(listaJogadores)}).encode(), endereco)
                
                # se há dois jogadores na listaJogadores, inicia o jogo
                if len(listaJogadores) == 2:
                    print("Dois jogadores conectados. Iniciando o jogo.")
                    # jogador 1 começa
                    s.sendto(json.dumps({"type": "game_start", "turno": True}).encode(), listaJogadores[0])
                    # jogador 2 começa
                    s.sendto(json.dumps({"type": "game_start", "turno": False}).encode(), listaJogadores[1])
            else:
                # se um terceiro jogador tentar se conectar, rejeita a conexão
                s.sendto(b"Servidor cheio.", endereco)
                print(f"Conexão rejeitada de {endereco}. Servidor cheio.")
            continue # ignora qualquer mensagem até o jogo começar
        
        # envio de mensagens durante o jogo
        if len(listaJogadores) == 2:

            # determina o endereço do oponente // se o endereço endereco é igual o indice zero então o indice um é o oponente
            if endereco == listaJogadores[0]:
                enderecoOponente = listaJogadores[1]
            else: # se não, o indice 0 da lista é o meu oponente
                enderecoOponente = listaJogadores[0]
            
            # envia nossa mensagem para o oponente
            print(f"Encaminhando mensagem de {endereco} para {enderecoOponente}")
            s.sendto(data, enderecoOponente)