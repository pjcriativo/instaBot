import threading
import time
from django.shortcuts import render
from instagrapi import Client
import openai
from PIL import Image, ImageDraw, ImageFont
from .forms import BotForm

# Definição das variáveis globais
bot_running = False
bot_thread = None
fotos_postadas = 0

def home_view(request):
    return render(request, 'painel_web/home.html')

def gerar_legenda(ideia, openai_key, gpt_model):
    with open('painel_web/prompts.txt', 'r') as file:
        prompts = dict(line.strip().split(':', 1) for line in file.readlines())
    
    prompt = prompts.get('cristao', "Você é do Instagram, você adora compartilhar conteúdo com seus seguidores")
    
    openai.api_key = openai_key
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Crie uma frase sobre {ideia}"}
        ]
    )
    return response['choices'][0]['message']['content']

def quebrar_texto(texto, fonte, largura_maxima, desenho):
    palavras = texto.split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        linha_teste = linha_atual + " " + palavra if linha_atual else palavra
        largura_texto, _ = desenho.textbbox((0, 0), linha_teste, font=fonte)[2:4]
        if largura_texto <= largura_maxima:
            linha_atual = linha_teste
        else:
            linhas.append(linha_atual)
            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    return "\n".join(linhas)

def criar_imagem_com_texto(largura, altura, cor_fundo, nome_arquivo, texto=None):
    imagem = Image.new("RGB", (largura, altura), cor_fundo)
    desenho = ImageDraw.Draw(imagem)

    if texto:
        try:
            fonte = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            fonte = ImageFont.load_default()

        texto_dividido = quebrar_texto(texto, fonte, largura - 40, desenho)
        bbox = desenho.textbbox((0, 0), texto_dividido, font=fonte)
        largura_texto = bbox[2] - bbox[0]
        altura_texto = bbox[3] - bbox[1]
        posicao_texto = ((largura - largura_texto) // 2, (altura - altura_texto) // 2)
        desenho.text(posicao_texto, texto_dividido, font=fonte, fill="white")

    imagem.save(nome_arquivo)
    return nome_arquivo

def postar_fotos(username, password, ideias, openai_key, gpt_model, intervalo_tempo):
    global fotos_postadas, bot_running

    cl = Client()
    try:
        cl.login(username, password)
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        return False  # Login failed

    first_post_successful = False

    while bot_running:
        for ideia in ideias:
            if not bot_running:
                break
            legenda = gerar_legenda(ideia.strip(), openai_key, gpt_model)
            imagem = criar_imagem_com_texto(800, 600, (0, 0, 0), "imagem_com_texto.png", legenda)

                        try:
                            cl.photo_upload(imagem, legenda)
                            fotos_postadas += 1
                            
                            
                        except Exception as e:
                            return render(request, 'painel_web/bot_form.html', {'form': form, 'error': f"Erro ao compartilhar a foto: {e}", 'fotos_postadas': fotos_postadas})\
                        
                        # render(request, 'painel_web/bot_form.html', {'form': form, 'message': f"Fotos postadas: {fotos_postadas}", 'fotos_postadas': fotos_postadas})

                        if(intervalo_tempo):
                            time.sleep(intervalo_tempo)
                        else:
                            time.sleep(300)
            except KeyboardInterrupt:# Permite que o loop seja interrompido manualmente
                pass                 

            
            try:
                cl.photo_upload(imagem, caption=legenda)
                fotos_postadas += 1
                print(f"Foto postada com sucesso: {legenda}")
                if not first_post_successful:
                    first_post_successful = True
            except Exception as e:
                print(f"Erro ao compartilhar a foto: {e}")
            
            time.sleep(intervalo_tempo)

    return first_post_successful

def iniciar_bot(username, password, ideias, openai_key, gpt_model, intervalo_tempo):
    global bot_running, bot_thread

    if not bot_running:
        bot_running = True
        bot_thread = threading.Thread(target=postar_fotos, args=(username, password, ideias, openai_key, gpt_model, intervalo_tempo))
        bot_thread.start()
        return True
    return False

def parar_bot():
    global bot_running
    bot_running = False
    print("Bot desligado.")

def bot_view(request):
    if request.method == 'POST':
        if 'start_bot' in request.POST:
            form = BotForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username', '') 
                password = form.cleaned_data.get('password', '')  
                ideias = form.cleaned_data.get('ideias', '').split(',')
                openai_key = form.cleaned_data.get('openai_key', '')  
                gpt_model = form.cleaned_data.get('gpt_model', '')  
                intervalo_tempo_minutos = int(form.cleaned_data.get('intervalo_tempo', 5))  
                intervalo_tempo_minutos = max(5, min(intervalo_tempo_minutos, 30))  
                intervalo_tempo = intervalo_tempo_minutos * 60 

                if iniciar_bot(username, password, ideias, openai_key, gpt_model, intervalo_tempo):
                    return render(request, 'painel_web/bot_form.html', {'form': form, 'message': "Foto postada"})
                else:
                    return render(request, 'painel_web/bot_form.html', {'form': form, 'message': "Erro ao iniciar o bot. Verifique suas credenciais."})

        elif 'stop_bot' in request.POST:
            parar_bot()
            return render(request, 'painel_web/bot_form.html', {'form': BotForm(), 'message': "Bot desligado com sucesso!"})
    else:
        form = BotForm(initial={ 
            'username': '', 
            'password': '', 
            'ideias': '',  
            'openai_key': '',  
            'gpt_model': '',  
            'intervalo_tempo': 5, 
        })
    return render(request, 'painel_web/bot_form.html', {'form': form})
