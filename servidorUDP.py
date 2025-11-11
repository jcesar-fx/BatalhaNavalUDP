import socket
import json
import random

HOST = '127.0.0.1'
PORT = 12345


partidas = {} # Lista que armazena as partidas abertas
mapa_jogadores = {} # Linka os jogadores com as partidas


def encontrar_partida_aberta():
    for id_partida, dados_partida in partidas.items():
        if dados_partida["estado"] == "ESPERANDO" and len(dados_partida["jogadores"]) == 1:
            return id_partida
    return None 

def remover_partida(id_partida):
    if id_partida in partidas:
        dados_partida = partidas[id_partida]
        for end_jogador in dados_partida["jogadores"]:
            if end_jogador in mapa_jogadores:
                del mapa_jogadores[end_jogador]
        del partidas[id_partida]
        # Printa que a partida foi removida do "lobby"
        print(f"[SISTEMA] Partida {id_partida} removida.")



with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Inicia o Servidor
    s.bind((HOST, PORT)) # parametros que inicia o servidor da biblioteca
    print(f"Servidor de Lobbies UDP escutando em {HOST}:{PORT}...")

    while True: #no laco de repeticao fica escutando as mensagens 
        data, endereco = s.recvfrom(1024) #byte do buffer de mensagem, pq ele fica lendo o que ta recebendo para ler
        # a partir disso verifica o que deve fazer 
        try: 
            msg = json.loads(data.decode())
            msg_type = msg.get("type")
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"[ERRO] Mensagem mal formatada de {endereco}")
            continue

        # Lógica de novo jogador \ a partir dessa mensagem ele vai definir oq e 
        if msg_type == "join":
            if endereco in mapa_jogadores:
                print(f"[AVISO] Jogador {endereco} tentou 'join' mas já está em uma partida.")
                continue

            id_partida_encontrada = encontrar_partida_aberta()

            if id_partida_encontrada:
                # Conseguiu fechar uma partida com 2 jogadores
                print(f"[LOBBY] Jogador {endereco} entrando na partida {id_partida_encontrada}")
                partida = partidas[id_partida_encontrada]
                partida["jogadores"].append(endereco)
                partida["estado"] = "EM_JOGO"
                
                mapa_jogadores[endereco] = id_partida_encontrada

                endereco_jogador_1 = partida["jogadores"][0]
                endereco_jogador_2 = partida["jogadores"][1]

                print(f"[LOBBY] Partida {id_partida_encontrada} iniciando: {endereco_jogador_1} vs {endereco_jogador_2}")
                
                s.sendto(json.dumps({"type": "game_start", "turno": True}).encode(), endereco_jogador_1)
                s.sendto(json.dumps({"type": "game_start", "turno": False}).encode(), endereco_jogador_2)
            
            else:
                # Cria uma nova partida para um jogador quando não há nenhuma partida aberta
                id_nova_partida = f"partida_{random.randint(0, 100)}"
                print(f"[LOBBY] Jogador {endereco} criando nova partida {id_nova_partida}")
                partidas[id_nova_partida] = {
                    "jogadores": [endereco],
                    "estado": "ESPERANDO"
                }
                mapa_jogadores[endereco] = id_nova_partida
                
                s.sendto(json.dumps({"type": "waiting_for_opponent"}).encode(), endereco)
        
        elif msg_type in ["tiro", "acerto", "erro", "game_over"]:
            # Verifica se a mensagem é uma mensagem válida
            if endereco not in mapa_jogadores:
                continue
            
            id_partida = mapa_jogadores[endereco]
            partida = partidas.get(id_partida) 

            if not partida or partida["estado"] != "EM_JOGO" or len(partida["jogadores"]) != 2:
                continue
            
            if endereco == partida["jogadores"][0]:
                endereco_oponente = partida["jogadores"][1]
            else:
                endereco_oponente = partida["jogadores"][0]
            
            # Mostra a mensagem sendo encaminhada
            print(f"[JOGO {id_partida}] Encaminhando '{msg_type}' de {endereco} para {endereco_oponente}")
            s.sendto(data, endereco_oponente)

            if msg_type == "game_over":
                print(f"[JOGO {id_partida}] Fim do jogo.")
                remover_partida(id_partida)
    
        elif msg_type == "leave":
            # Desconecta o jogador da partida
            if endereco in mapa_jogadores:
                id_partida = mapa_jogadores[endereco]
                partida = partidas.get(id_partida)

                if not partida:
                    continue 

                print(f"[LOBBY] Jogador {endereco} desconectou da partida {id_partida}.")

                if partida["estado"] == "EM_JOGO" and len(partida["jogadores"]) == 2:
                    if endereco == partida["jogadores"][0]:
                        endereco_oponente = partida["jogadores"][1]
                    else:
                        endereco_oponente = partida["jogadores"][0]
                    
                    # Avisa que o oponente foi notificado da desistência do adversário
                    print(f"[LOBBY {id_partida}] Avisando {endereco_oponente} que o oponente saiu.")
                    s.sendto(json.dumps({"type": "opponent_disconnected"}).encode(), endereco_oponente)
                
                remover_partida(id_partida)