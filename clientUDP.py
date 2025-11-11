import pygame
import socket
import json
from logicaBatalhaNaval import iniciarBatalhao

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 600
GRID_SIZE = 40
MARGIN = 5
FONT_SIZE = 20

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (104, 207, 239) 
GREEN = (0, 255, 0)    
RED = (255, 0, 0)      
ORANGE = (255, 165, 0) 

MY_GRID_OFFSET_X, MY_GRID_OFFSET_Y = 50, 100
ENEMY_GRID_OFFSET_X, ENEMY_GRID_OFFSET_Y = 650, 100

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Batalha Naval")
font = pygame.font.Font(None, FONT_SIZE)
big_font = pygame.font.Font(None, 40)

BOTAO_JOGAR_NOVAMENTE_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 125, SCREEN_HEIGHT // 2 + 50, 250, 50) 

# Configuração do socket UDP
HOST = '127.0.0.1'
PORT = 12345
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setblocking(False) 

meu_batalhao = iniciarBatalhao()
meus_tiros = set()
danos_inimigos = set()
tiros_inimigos = set()
meu_turno = False
game_over = False
mensagem = "Procurando partida..."

def desenha_os_grids(offset_x, offset_y, titulo, show_ships=False):
    # Estrutura o mapa do jogo para ser desenhado na tela
    tituloPrincipal = big_font.render(titulo, True, BLACK)
    screen.blit(tituloPrincipal, (offset_x, offset_y - 50))

    for linha in range(10):
        for coluna in range(10):
            if linha == 0:
                coluna_label = font.render(str(coluna + 1), True, BLACK)
                screen.blit(coluna_label, (offset_x + coluna * (GRID_SIZE + MARGIN) + GRID_SIZE // 2, offset_y - 20))
            if coluna == 0:
                linha_label = font.render(chr(ord('A') + linha), True, BLACK)
                screen.blit(linha_label, (offset_x - 20, offset_y + linha * (GRID_SIZE + MARGIN) + GRID_SIZE // 2))

            rect = pygame.Rect(offset_x + coluna * (GRID_SIZE + MARGIN),
                               offset_y + linha * (GRID_SIZE + MARGIN),
                               GRID_SIZE, GRID_SIZE)
            
            cor = BLUE 

            if show_ships: 
                if (linha, coluna) in meu_batalhao:
                    cor = GREEN
                if (linha, coluna) in tiros_inimigos:
                    cor = BLACK if (linha, coluna) in meu_batalhao else RED
            else: 
                if (linha, coluna) in danos_inimigos:    
                    cor = ORANGE             
                elif (linha, coluna) in meus_tiros:  
                    cor = RED
            
            pygame.draw.rect(screen, cor, rect)

def enviar_mensagem(msg_type, data):
    # Envia uma mensagem formatada em JSON para o servidor.
    mensagem_json = json.dumps({"type": msg_type, "data": data})
    client_socket.sendto(mensagem_json.encode(), (HOST, PORT))
    # Imprime no terminal do cliente o que foi enviado
    print(f"[ENVIOU] -> Tipo: {msg_type}, Dados: {data}")

def botao_jogar_novamente():
    pygame.draw.rect(screen, BLUE, BOTAO_JOGAR_NOVAMENTE_RECT, border_radius=10) 
    texto_botao = big_font.render("Jogar Novamente", True, BLACK)
    texto_rect = texto_botao.get_rect(center=BOTAO_JOGAR_NOVAMENTE_RECT.center)
    screen.blit(texto_botao, texto_rect)

def reiniciar_jogo():
    global meu_batalhao, meus_tiros, danos_inimigos, tiros_inimigos, meu_turno, game_over, mensagem
    
    meu_batalhao = iniciarBatalhao()
    meus_tiros = set()
    danos_inimigos = set()
    tiros_inimigos = set()
    meu_turno = False
    game_over = False
    mensagem = "Procurando partida..."
    
    enviar_mensagem("join", "")


# Lógica do jogo rodando
enviar_mensagem("join", "") 
rodando = True
while rodando:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if not game_over: 
                enviar_mensagem("leave", "") 
            rodando = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            
            if game_over:
                if BOTAO_JOGAR_NOVAMENTE_RECT.collidepoint(pos):
                    reiniciar_jogo()
                    continue 
            
            if meu_turno and not game_over:
                if ENEMY_GRID_OFFSET_X < pos[0] < ENEMY_GRID_OFFSET_X + 10 * (GRID_SIZE + MARGIN) and \
                   ENEMY_GRID_OFFSET_Y < pos[1] < ENEMY_GRID_OFFSET_Y + 10 * (GRID_SIZE + MARGIN):
                    
                    coluna = (pos[0] - ENEMY_GRID_OFFSET_X) // (GRID_SIZE + MARGIN)
                    linha = (pos[1] - ENEMY_GRID_OFFSET_Y) // (GRID_SIZE + MARGIN)
                    
                    if (linha, coluna) not in meus_tiros:
                        meus_tiros.add((linha, coluna))
                        enviar_mensagem("tiro", (linha, coluna))
                        meu_turno = False 

    # Troca de mensagens
    try:
        while True: 
            data, addr = client_socket.recvfrom(1024) 
            msg = json.loads(data.decode())
            
            # Imprime no terminal do cliente o que foi recebido
            print(f"[RECEBEU] <- {msg}")

            msg_type = msg.get("type")
            msg_data = msg.get("data")

            if msg_type == "waiting_for_opponent":
                mensagem = "Esperando por um oponente..."
            
            elif msg_type == "game_start":
                meu_turno = msg.get("turno")
                mensagem = "Seu turno!" if meu_turno else "Turno do oponente."
            
            elif msg_type == "tiro":
                coordenada_tiro = tuple(msg_data)
                tiros_inimigos.add(coordenada_tiro)
                
                if coordenada_tiro in meu_batalhao:        
                    enviar_mensagem("acerto", coordenada_tiro) 
                    
                    if all(parte_navio in tiros_inimigos for parte_navio in meu_batalhao):
                        enviar_mensagem("game_over", "Você venceu!")
                        mensagem = "Você Perdeu!"
                        game_over = True
                else:
                    enviar_mensagem("erro", coordenada_tiro)
                
                if not game_over:
                    meu_turno = True
                    mensagem = "Seu turno!"

            elif msg_type == "acerto":
                coordenada_tiro = tuple(msg_data)
                danos_inimigos.add(coordenada_tiro)
                rect_x = ENEMY_GRID_OFFSET_X + coordenada_tiro[1] * (GRID_SIZE + MARGIN)
                rect_y = ENEMY_GRID_OFFSET_Y + coordenada_tiro[0] * (GRID_SIZE + MARGIN)
                pygame.draw.rect(screen, ORANGE, (rect_x, rect_y, GRID_SIZE, GRID_SIZE))

            elif msg_type == "game_over":
                mensagem = msg_data
                game_over = True
                meu_turno = False

            elif msg_type == "opponent_disconnected":
                mensagem = "Oponente desconectou. Você venceu!"
                game_over = True
                meu_turno = False

    except BlockingIOError:
        pass

    # Desenha o jogo na tela
    screen.fill(WHITE)
    
    if not game_over:
        desenha_os_grids(MY_GRID_OFFSET_X, MY_GRID_OFFSET_Y, "Seu Batalhão", show_ships=True)
        desenha_os_grids(ENEMY_GRID_OFFSET_X, ENEMY_GRID_OFFSET_Y, "Batalhão Inimigo")
    
    status_surface = big_font.render(mensagem, True, BLACK)
    if game_over:
        screen.blit(status_surface, (SCREEN_WIDTH // 2 - status_surface.get_width() // 2, SCREEN_HEIGHT // 2 - status_surface.get_height() // 2 - 20)) 
    else:
        screen.blit(status_surface, (SCREEN_WIDTH // 2 - status_surface.get_width() // 2, 20))

    if game_over:
        botao_jogar_novamente()

    pygame.display.flip()

pygame.quit()
client_socket.close()