import random

# cria os navios de certo tamanho e retorna uma lusta de coordenadas
def criarNavio(tamanhoDoNavio, coordenadasExistentes):
    while True:
        # 1 = cima, 2 = baixo, 3 = esquerda, 4 = direita
        direcaoDeCrescimentoDoNavio = random.randint(1, 4)
        
        linhaDeOrigem = random.randint(0, 9)
        colunaDeOrigem = random.randint(0, 9)

        coordenasDoBarco = []
        valido = True

        for i in range(tamanhoDoNavio):
            linha, coluna = linhaDeOrigem, colunaDeOrigem
            if direcaoDeCrescimentoDoNavio == 1: # Up
                linha -= i
            elif direcaoDeCrescimentoDoNavio == 2: # Down
                linha += i
            elif direcaoDeCrescimentoDoNavio == 3: # Left
                coluna -= i
            elif direcaoDeCrescimentoDoNavio == 4: # Right
                coluna += i
            
            # verifica que o navio está dentro dos limites do tabuleiro e não colide com outros navios
            if not (0 <= linha <= 9 and 0 <= coluna <= 9) or (linha, coluna) in coordenadasExistentes:
                valido = False
                break
            
            coordenasDoBarco.append((linha, coluna))
        
        if valido:
            return coordenasDoBarco
# gera os navios iniciais de tamanho 3, 2 e 1
def iniciarBatalhao():
    
    todasCoordenadasDoBatalhao = set()
    
    # cria um navio de tamanho 3
    coordNavio3 = criarNavio(3, todasCoordenadasDoBatalhao)
    for coord in coordNavio3:
        todasCoordenadasDoBatalhao.add(coord)
    
    # cria um navio de tamanho 2
    coordNavio2 = criarNavio(2, todasCoordenadasDoBatalhao)
    for coord in coordNavio2:
        todasCoordenadasDoBatalhao.add(coord)

    # cria um navio de tamanho 1
    coordNavio1 = criarNavio(1, todasCoordenadasDoBatalhao)
    for coord in coordNavio1:
        todasCoordenadasDoBatalhao.add(coord)
        
    # retorna uma lista com todas as coordenadas do batalhão
    return list(todasCoordenadasDoBatalhao)