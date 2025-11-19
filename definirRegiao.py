from pynput import mouse
import time
import pygetwindow as gw
import os

# Carrega variáveis simples de um .env local (FORMATO: KEY=VALUE)
def load_env(path='.env'):
    data = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return data

def write_env_var(key, value, path='.env'):
    # lê linhas existentes
    lines = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        lines = []

    found = False
    new_lines = []
    for line in lines:
        if not line or line.strip().startswith('#') or '=' not in line:
            new_lines.append(line)
            continue
        k, _ = line.split('=', 1)
        if k.strip() == key:
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

# Nome da janela (padrão se não existir no .env)
_env = load_env()
NOME_JANELA = _env.get('NOME_JANELA', 'Bloco de Notas')

coordenadas_cliques = [] # Lista para guardar os 2 cliques

def on_click(x, y, button, pressed):
    """Função chamada automaticamente quando o mouse é clicado"""
    if pressed:
        print(f"Clique detectado em: x={x}, y={y}")
        coordenadas_cliques.append((x, y))
        
        # Se já temos 2 cliques, paramos de escutar
        if len(coordenadas_cliques) >= 2:
            return False # Retornar False para o listener

def definir_regiao_manualmente(janela):
    """Gerencia o processo de focar a janela e pegar os cliques"""
    print("\n--- INICIANDO CALIBRAÇÃO ---")
    
    # 1. Focar na janela
    try:
        if janela.isMinimized:
            janela.restore()
        janela.activate()
        time.sleep(1) 
    except Exception as e:
        print(f"Erro ao focar janela: {e}")

    print(f"A janela '{NOME_JANELA}' foi focada.")
    print("PASSO 1: Clique no CANTO SUPERIOR ESQUERDO da área que deseja ler.")
    print("PASSO 2: Clique no CANTO INFERIOR DIREITO da área que deseja ler.")
    
    # 2. Iniciar o Listener (Escuta do mouse)
    # O código vai ficar 'preso' aqui até você dar os 2 cliques
    # limpar cliques anteriores caso o módulo já tenha sido usado
    coordenadas_cliques.clear()
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
        
    # 3. Calcular a região (Left, Top, Width, Height)
    x1, y1 = coordenadas_cliques[0]
    x2, y2 = coordenadas_cliques[1]

    # Garantir que x1 seja menor que x2 (caso você clique invertido)
    esquerda = min(x1, x2)
    topo = min(y1, y2)
    largura = abs(x2 - x1)
    altura = abs(y2 - y1)
    
    regiao = (esquerda, topo, largura, altura)
    print(f"\nRegião definida: {regiao}")
    # salvar no .env para ser reutilizada por outros módulos
    try:
        write_env_var('REGIAO', ','.join(map(str, regiao)))
        print("Região salva em '.env' na chave REGIAO.")
    except Exception as e:
        print(f"Erro ao salvar região no .env: {e}")

    return regiao

def main():
    print("Iniciando Macro...")
    
    # 1. Focar na Janela
    try:
        janela = gw.getWindowsWithTitle(NOME_JANELA)[0]
        if janela.isMinimized:
            janela.restore()
        janela.activate()
        time.sleep(1) # Esperar a janela vir para frente
    except IndexError:
        print(f"Janela '{NOME_JANELA}' não encontrada.")
        return
    
    regiao_escolhida = definir_regiao_manualmente(janela)

if __name__ == "__main__":
    main()