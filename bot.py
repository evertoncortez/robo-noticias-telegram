import feedparser
import requests
import os
from datetime import datetime
import random

# === CONFIGURAÇÕES ===
# As credenciais agora serão lidas das "Secrets" do GitHub
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Nome do arquivo que guardará os links já enviados
ARQUIVO_DE_LINKS_ENVIADOS = "sent_links.txt"

# === FONTES RSS ===
RSS_FEEDS = [
    "https://www.tecmundo.com.br/feeds/rss",
    "https://www.canaltech.com.br/rss/",
    "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml",
    "https://agenciabrasil.ebc.com.br/rss/geral/feed.xml",
    "https://feeds.folha.uol.com.br/ciencia/rss091.xml",
    "https://g1.globo.com/rss/g1/tecnologia/",
    "https://olhardigital.com.br/feed/"
]

# === PALAVRAS-CHAVE ===
KEYWORDS = ["tecnologia", "ciência", "inteligência artificial", "inovação", "uber", "meta", "facebook", "biometria", "anatel", "starlink", "game", "jogo", "videogame", "celular", "smartphone", "android", "ios", "pc", "console", "lua", "fórmula 1", "robô", "kindle", "samsung", "tv", "amd", "intel", "galaxy", "apple", "nvidia", "chatgpt", "gemini", "nasa", "ia", "telescópio", "microsoft"]

# === Funções para persistência de dados ===
def carregar_links_enviados():
    """Lê o arquivo de texto e carrega os links para um set."""
    try:
        with open(ARQUIVO_DE_LINKS_ENVIADOS, 'r') as f:
            # Usamos um set para performance e para evitar duplicados na checagem
            return set(line.strip() for line in f)
    except FileNotFoundError:
        # Se o arquivo não existe, retorna um set vazio
        return set()

def salvar_link_enviado(link):
    """Adiciona um novo link ao final do arquivo de texto."""
    with open(ARQUIVO_DE_LINKS_ENVIADOS, 'a') as f:
        f.write(link + '\n')

# === Função para logs com timestamp ===
def log(mensagem):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensagem}")

# === Buscar notícias do RSS ===
def filtrar_noticias(feed_url, sent_links):
    noticias = []
    try:
        feed = feedparser.parse(feed_url)
        for item in feed.entries:
            titulo = item.title.lower()
            link = item.link

            if link in sent_links:
                continue # Pula para o próximo item se o link já foi enviado

            # Verifica se QUALQUER palavra-chave está no título
            if any(palavra.lower() in titulo for palavra in KEYWORDS):
                log(f"✅ Notícia relevante: {item.title}")
                noticias.append({"title": item.title, "link": link})

    except Exception as e:
        log(f"❌ Erro ao processar o feed {feed_url}: {e}")
    return noticias

# === Enviar mensagem no Telegram ===
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "disable_web_page_preview": False}
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status() # Lança um erro se a requisição falhar
        log(f"📤 Mensagem enviada para o Telegram.")
        return True
    except requests.exceptions.RequestException as e:
        log(f"❌ Erro ao enviar para Telegram: {e}")
        return False

# === Função principal do bot ===
def executar_bot():
    log("🚀 Robô iniciado!")
    
    if not TOKEN or not CHAT_ID:
        log("❌ ERRO: Variáveis de ambiente TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID não foram configuradas.")
        return

    links_ja_enviados = carregar_links_enviados()
    log(f"🧠 Memória carregada com {len(links_ja_enviados)} links.")
    
    novas_noticias = []
    for rss in RSS_FEEDS:
        noticias_filtradas = filtrar_noticias(rss, links_ja_enviados)
        novas_noticias.extend(noticias_filtradas)
        log(f"🌐 {len(noticias_filtradas)} nova(s) notícia(s) encontrada(s) em: {rss}")

    if not novas_noticias:
        log("✅ Nenhuma notícia nova encontrada desta vez. Encerrando.")
    else:
        random.shuffle(novas_noticias) # Embaralha para variar a ordem
        enviadas_com_sucesso = 0
        for noticia in novas_noticias:
            mensagem = f"📰 {noticia['title']}\n\n🔗 {noticia['link']}"
            if enviar_telegram(mensagem):
                salvar_link_enviado(noticia['link']) # Salva no arquivo SÓ se o envio der certo
                enviadas_com_sucesso += 1

        log(f"✅ Tarefa concluída! {enviadas_com_sucesso} de {len(novas_noticias)} notícias foram enviadas.")

# === EXECUÇÃO PRINCIPAL ===
# Esta parte será chamada pelo GitHub Actions
if __name__ == "__main__":
    executar_bot()
