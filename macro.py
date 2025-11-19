import pyautogui
import pytesseract
import pygetwindow as gw
import cv2
import numpy as np
import time
import threading
from pynput import keyboard
from PIL import Image
import os

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
    except Exception:
        return {}
    return data

# carregamos .env já feito acima
_env = load_env()

# Nome exato ou parcial da janela do aplicativo (prioriza .env)
NOME_JANELA = _env.get('NOME_JANELA', "Bloco de Notas")

# --- CONFIGURAÇÃO ---
# Apontar para o executável do Tesseract (ajuste este caminho conforme sua instalação)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# (NOME_JANELA já é lido do .env acima; valor padrão é 'Bloco de Notas')

# Segurança: Arraste o mouse para o canto superior esquerdo para abortar o script
pyautogui.FAILSAFE = True 

def picareta(janela):
    print("trocando por picareta")
    return '4' # Retorna True para avisar que acabou

def machado(janela):
    print("trocando por machado")
    return '2' # Retorna True para avisar que acabou

def pa(janela):
    print("trocando por pa")
    return '3' # Retorna True para avisar que acabou

def tesoura(janela):
    print("trocando por tesoura")
    return '5' # Retorna True para avisar que acabou

def enxada(janela):
    print("trocando por enxada")
    return '6'

def decidir_acao(texto_lido, janela):
    # Convertemos para minúsculo para facilitar a comparação
    texto = texto_lido.lower()
    tool = '';

    # CASO 1: LOGIN
    # Podemos checar várias palavras que indicam a mesma coisa
    if "pickaxe" in texto:
        tool = picareta(janela)

    # CASO 2: ERRO
    elif "axe" in texto:
        tool = machado(janela)

    # CASO 3: SUCESSO
    elif "shovel" in texto:
        tool = pa(janela)

    # CASO 4: NADA ENCONTRADO
    else:
        print("Nenhuma palavra-chave conhecida encontrada. Aguardando...")
        return False
    
    if (tool != ''):
        pyautogui.press('Esc')
        pyautogui.press(tool)
        # mover para o centro da TELA e manter pressionado por 1 segundo
        screen_w, screen_h = pyautogui.size()
        x_center, y_center = screen_w // 2, screen_h // 2
        pyautogui.moveTo(x_center, y_center)
        pyautogui.mouseDown()
        try:
            click_duration = int(_env.get('CLICK_DURATION') or 1)
        except Exception:
            click_duration = 1
        time.sleep(click_duration)
        pyautogui.mouseUp()
        return True
    
def processar_imagem_para_ocr(imagem):
    """Converte o print para escala de cinza e aumenta contraste para o OCR ler melhor"""
    # Converter imagem do PIL para formato OpenCV
    img = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2BGR)
    
    # Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar limiarização (deixar tudo preto ou branco)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

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

    # 2. Definimos a região (left, top, width, height)
    # Primeiro tentamos carregar a região salva em '.env' (chave REGIAO)
    regiao_escolhida = None
    try:
        env = load_env()
        reg = env.get('REGIAO')
        if reg:
            partes = [p.strip() for p in reg.split(',') if p.strip() != '']
            if len(partes) == 4:
                regiao_escolhida = tuple(int(p) for p in partes)
                print(f"Região carregada de '.env': {regiao_escolhida}")
            else:
                print("Valor REGIAO no .env inválido. Será feita a calibração manual.")
        else:
            print("REGIAO não definida no .env. Iniciando calibração manual.")
    except Exception as e:
        print(f"Erro ao ler '.env': {e}. Irei calibrar manualmente.")

    # Se não conseguimos carregar a região, cair para calibração manual
    if regiao_escolhida is None:
        try:
            from definirRegiao import definir_regiao_manualmente
        except Exception:
            print("Não foi possível importar 'definir_regiao_manualmente' de 'definirRegiao'.")
            raise
        regiao_escolhida = definir_regiao_manualmente(janela)

    # Lê duração em minutos do .env (chaves suportadas: RUN_MINUTES, MINUTOS, DURACAO_MINUTOS)
    try:
        env = load_env()
        run_val = env.get('RUN_MINUTES') or env.get('MINUTOS') or env.get('DURACAO_MINUTOS')
        run_minutes = float(run_val) if run_val is not None else 5.0
    except Exception:
        run_minutes = 5.0

    # Configurar listener de teclado (F12 para parar)
    stop_event = threading.Event()

    def _on_key_press(key):
        try:
            if key == keyboard.Key.f12:
                print("Tecla F12 detectada: interrompendo o macro...")
                stop_event.set()
        except Exception:
            pass

    kb_listener = keyboard.Listener(on_press=_on_key_press)
    kb_listener.daemon = True
    kb_listener.start()

    end_time = time.time() + run_minutes * 60.0
    print(f"Executando ciclo por {run_minutes} minutos (pressione F12 para parar).")

    # Loop principal: realizar capturas e decidir ações até o tempo expirar ou o usuário pedir stop
    while time.time() < end_time and not stop_event.is_set():
        screenshot = pyautogui.screenshot(region=regiao_escolhida)
        # (Opcional) salvar debug — sobrescreve a cada ciclo
        screenshot.save("debug_print.png")

        imagem_processada = processar_imagem_para_ocr(screenshot)
        texto_extraido = pytesseract.image_to_string(imagem_processada, lang='eng')
        decidir_acao(texto_extraido, janela)

        # pequena pausa para evitar loop extremamente rápido
        time.sleep(0.5)

    # Encerrar listener
    try:
        kb_listener.stop()
    except Exception:
        pass

    if stop_event.is_set():
        print("Macro interrompido pelo usuário (F12).")
    else:
        print("Tempo de execução expirado. Macro finalizado.")
    # Fim do main: loop já efetuou os ciclos necessários

if __name__ == "__main__":
    main()