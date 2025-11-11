import pygame
import socket
import json
from logicaBatalhaNaval import iniciarBatalhao

# define tamanho de tela, grid, margens e tamanho das fontes
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 600
GRID_SIZE = 40
MARGIN = 5
FONT_SIZE = 20

# cores usadas no pygame
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (104, 207, 239) # cor da agua
GREEN = (0, 255, 0)    # cor dos seus navios
RED = (255, 0, 0)      # cor do tiro errado
ORANGE = (255, 165, 0) # cor do acerto

# alinhamento dos grids
MY_GRID_OFFSET_X, MY_GRID_OFFSET_Y = 50, 100
ENEMY_GRID_OFFSET_X, ENEMY_GRID_OFFSET_Y = 650, 100


# inicialização padrão do pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Batalha Naval")
font = pygame.font.Font(None, FONT_SIZE)
big_font = pygame.font.Font(None, 40)

# CONFIGURAÇÃO do socket UDP
HOST = '127.0.0.1'
PORT = 12345
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client_socket.setblocking(False) # se não houver dados, não bloqueia a execução

meu_batalhao = iniciarBatalhao()
meus_tiros = set()
danos_inimigos = set()
tiros_inimigos = set()
meu_turno = False
game_over = False
mensagem = "Conectando ao servidor..."

# faz o grid 10x10 com todos seus detalhes, titulo, navios, labels e etc...
def desenhaOsGrids(offset_x, offset_y, titulo, show_ships=False):
    tituloPrincipal = big_font.render(titulo, True, BLACK)
    screen.blit(tituloPrincipal, (offset_x, offset_y - 50))

    for linha in range(10):
        for coluna in range(10):
            # desenha os nomes das linhas e colunas

            # se linha for 0 desenha os números das colunas
            # se coluna for 0 desenha as letras das linhas
            if linha == 0:
                coluna_label = font.render(str(coluna + 1), True, BLACK)
                screen.blit(coluna_label, (offset_x + coluna * (GRID_SIZE + MARGIN) + GRID_SIZE // 2, offset_y - 20))
            if coluna == 0:
                linha_label = font.render(chr(ord('A') + linha), True, BLACK)
                screen.blit(linha_label, (offset_x - 20, offset_y + linha * (GRID_SIZE + MARGIN) + GRID_SIZE // 2))

            # desenha cada célula retangular do grid 
            rect = pygame.Rect(offset_x + coluna * (GRID_SIZE + MARGIN),
                               offset_y + linha * (GRID_SIZE + MARGIN),
                               GRID_SIZE, GRID_SIZE)
            
            colunaor = BLUE

            # se for o "Seu Batalhão"
            if show_ships:
                if (linha, coluna) in meu_batalhao:
                    colunaor = GREEN
                if (linha, coluna) in tiros_inimigos: # Shots taken by the enemy on my board
                    colunaor = ORANGE if (linha, coluna) in meu_batalhao else RED
            # Logica for "Batalhão Inimigo"
            # Logic for "Batalhão Inimigo"
            else:
                if (linha, coluna) in danos_inimigos:    
                    colunaor = ORANGE             
                elif (linha, coluna) in meus_tiros:  
                    colunaor = RED
            
            pygame.draw.rect(screen, colunaor, rect)

# envia mensagem para o servidor UDP em formato JSON
def enviar_mensagem(msg_type, data):
    mensagem = json.dumps({"type": msg_type, "data": data})
    client_socket.sendto(mensagem.encode(), (HOST, PORT))

# logica principal do jogo
enviar_mensagem("connect", "") # inicia a conexão com o servidor
rodando = True
while rodando:
    # para cada evento do pygame se já for para fechar a janela ou clicar no grid inimigo faz a ação correspondente
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

        # faz a parte do clique do mouse para atirar se for o meu turno e o jogo não tiver acabado
        if event.type == pygame.MOUSEBUTTONDOWN and meu_turno and not game_over:
            pos = pygame.mouse.get_pos()
            
            # ve se o evento de clique foi dentro do grid inimigo
            if ENEMY_GRID_OFFSET_X < pos[0] < ENEMY_GRID_OFFSET_X + 10 * (GRID_SIZE + MARGIN) and \
               ENEMY_GRID_OFFSET_Y < pos[1] < ENEMY_GRID_OFFSET_Y + 10 * (GRID_SIZE + MARGIN):
                
                coluna = (pos[0] - ENEMY_GRID_OFFSET_X) // (GRID_SIZE + MARGIN)
                linha = (pos[1] - ENEMY_GRID_OFFSET_Y) // (GRID_SIZE + MARGIN)
                
                # envia o tiro se ainda não tiver atirado nessa coordenada
                if (linha, coluna) not in meus_tiros:
                    meus_tiros.add((linha, coluna))
                    enviar_mensagem("tiro", (linha, coluna))
                    meu_turno = False # End turn after shooting

    # recebe mensagens do servidor UDP
    try:
        while True: #enquanto true, tenta receber todas as mensagens disponíveis
            data, addr = client_socket.recvfrom(1024) # tenta ler 1024 bytes da mensagem recebida
            msg = json.loads(data.decode())
            msg_type = msg.get("type")
            msg_data = msg.get("data")

            if msg_type == "connected":
                # le diretamente da msg não de msg_data
                mensagem = f"Conectado! Você é o jogador {msg['numero_jogador']}. Esperando oponente..."
            
            elif msg_type == "game_start":
                # novametne le diretamente da msg não de msg_data
                meu_turno = msg["turno"]
                mensagem = "Seu turno!" if meu_turno else "Turno do oponente."
            
            elif msg_type == "tiro":
                coordenada_tiro = tuple(msg_data)
                tiros_inimigos.add(coordenada_tiro)
                
                # se a coordenado do tiro foi no meu batalhão, é um acerto do inimigo
                if coordenada_tiro in meu_batalhao:
                    enviar_mensagem("acerto", coordenada_tiro) #avisa ele que ele acertou
                    # ve se eu ainda tenho partes do navio restantes, se não, o jogo acaba e eu perdi
                    if all(parte_navio in tiros_inimigos for parte_navio in meu_batalhao):
                        enviar_mensagem("game_over", "Você venceu!")
                        mensagem = "Você Perdeu!"
                        game_over = True
                else:
                    enviar_mensagem("erro", coordenada_tiro)
                
                # se o jogo não acabou, é meu turno
                if not game_over:
                    meu_turno = True
                    mensagem = "Seu turno!"

            elif msg_type == "acerto":
                #Marca a parte do navio inimigo que foi atingida
                coordenada_tiro = tuple(msg_data)
                danos_inimigos.add(coordenada_tiro)
                rect_x = ENEMY_GRID_OFFSET_X + coordenada_tiro[1] * (GRID_SIZE + MARGIN)
                rect_y = ENEMY_GRID_OFFSET_Y + coordenada_tiro[0] * (GRID_SIZE + MARGIN)
                pygame.draw.rect(screen, ORANGE, (rect_x, rect_y, GRID_SIZE, GRID_SIZE))

            elif msg_type == "game_over":
                mensagem = msg_data
                game_over = True
                meu_turno = False

    except BlockingIOError:
        # entra aqui quando não há mensagems para ler
        pass

    # desenha o fundo e o grid do jogo
    screen.fill(WHITE)
    desenhaOsGrids(MY_GRID_OFFSET_X, MY_GRID_OFFSET_Y, "Seu Batalhão", show_ships=True)
    desenhaOsGrids(ENEMY_GRID_OFFSET_X, ENEMY_GRID_OFFSET_Y, "Batalhão Inimigo")
    
    # desenha a mensagem de status no topo da tela
    status_surface = big_font.render(mensagem, True, BLACK)
    screen.blit(status_surface, (SCREEN_WIDTH // 2 - status_surface.get_width() // 2, 20))

    pygame.display.flip()

pygame.quit()