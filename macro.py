import pyautogui
import pytesseract
import pygetwindow as gw
import cv2
import numpy as np
import time
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
    pyautogui.click(janela.width / 2, janela.height / 2) 
    pyautogui.press('4')
    return True # Retorna True para avisar que acabou

def machado(janela):
    print("trocando por machado")
    pyautogui.click(janela.width / 2, janela.height / 2) 
    pyautogui.press('2')
    return True # Retorna True para avisar que acabou

def pa(janela):
    print("trocando por pa")
    pyautogui.click(janela.width / 2, janela.height / 2) 
    pyautogui.press('3')
    return True # Retorna True para avisar que acabou

def tesoura(janela):
    print("trocando por tesoura")
    pyautogui.click(janela.width / 2, janela.height / 2) 
    pyautogui.press('5')
    return True # Retorna True para avisar que acabou

def enxada(janela):
    print("trocando por enxada")
    pyautogui.click(janela.width / 2, janela.height / 2) 
    pyautogui.press('6')
    return True

def decidir_acao(texto_lido, janela):
    # Convertemos para minúsculo para facilitar a comparação
    texto = texto_lido.lower()

    # CASO 1: LOGIN
    # Podemos checar várias palavras que indicam a mesma coisa
    if "pickaxe" in texto:
        picareta(janela)
        return False # Continua o script

    # CASO 2: ERRO
    elif "axe" in texto:
        machado(janela)
        return False

    # CASO 3: SUCESSO
    elif "shovel" in texto:
        pa(janela)
        return False

    # CASO 4: NADA ENCONTRADO
    else:
        print("Nenhuma palavra-chave conhecida encontrada. Aguardando...")
        return False
    
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
    screenshot = pyautogui.screenshot(region=regiao_escolhida)
    
    screenshot.save("debug_print.png")

    # 3. Ler o texto (OCR)
    # Processamos a imagem para o computador entender melhor
    imagem_processada = processar_imagem_para_ocr(screenshot)
    
    # Extrair texto (lang='por' para português, precisa instalar o pacote de idioma no Tesseract)
    texto_extraido = pytesseract.image_to_string(imagem_processada, lang='eng') # Use 'por' se instalou
    
    processo_finalizado = decidir_acao(texto_extraido, janela)

    if processo_finalizado:
        print("Saindo do Macro.")

if __name__ == "__main__":
    main()