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
# Todas as palavras devem estar em minúsculas para a comparação funcionar corretamente.
KEYWORDS = [
    "tecnologia", "ciência", "inteligência artificial", "inovação", "uber", 
    "meta", "facebook", "biometria", "anatel", "starlink", "game", "jogo", 
    "videogame", "celular", "smartphone", "android", "ios", "pc", "console", 
    "lua", "fórmula 1", "robô", "kindle", "samsung", "tv", "amd", "intel", 
    "galaxy", "apple", "nvidia", "chatgpt", "gemini", "nasa", "ia", 
    "telescópio", "microsoft"
]

# === Funções para persistência de dados ===
def carregar_links_enviados():
    """Lê o arquivo de texto e carrega os links para um set."""
    try:
        with open(ARQUIVO_DE_LINKS_ENVIADOS, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def salvar_link_enviado(link):
    """Adiciona um novo link ao final do arquivo de texto."""
    with open(ARQUIVO_DE_LINKS_ENVIADOS, 'a', encoding='utf-8') as f:
        f.write(link + '\n')

# === Função para logs com timestamp ===
def log(mensagem):
    """Imprime uma mensagem de log formatada com data e hora."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensagem}")

# === Buscar notícias do RSS ===
def filtrar_noticias(feed_url, sent_links):
    """Busca notícias em um feed, filtra por palavras-chave e remove duplicatas."""
    noticias_relevantes = []
    try:
        feed = feedparser.parse(feed_url)
        for item in feed.entries:
            titulo = item.title.lower()
            link = item.link

            if link in sent_links:
                continue

            # Verifica se QUALQUER palavra-chave está no título
            if any(palavra in titulo for palavra in KEYWORDS):
                log(f"✅ Notícia relevante encontrada: {item.title}")
                noticias_relevantes.append({"title": item.title, "link": link})
            else:
                # MELHORIA: Log para notícias que não passaram no filtro
                log(f"❌ Notícia ignorada (sem palavras-chave): {item.title}")

    except Exception as e:
        log(f"❌ Erro ao processar o feed {feed_url}: {e}")
    return noticias_relevantes

# === Enviar mensagem no Telegram ===
def enviar_telegram(mensagem):
    """Envia uma mensagem de texto para o chat configurado no Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "disable_web_page_preview": False}
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        log("📤 Mensagem enviada para o Telegram.")
        return True
    except requests.exceptions.RequestException as e:
        log(f"❌ Erro ao enviar para Telegram: {e}")
        return False

# === Função principal do bot ===
def executar_bot():
    """Orquestra a execução completa do robô."""
    log("🚀 Robô iniciado!")
    
    if not TOKEN or not CHAT_ID:
        log("❌ ERRO CRÍTICO: As variáveis de ambiente TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID não foram configuradas nas Secrets do GitHub.")
        return

    links_ja_enviados = carregar_links_enviados()
    log(f"🧠 Memória carregada com {len(links_ja_enviados)} links.")
    
    todas_as_novas_noticias = []
    for rss_url in RSS_FEEDS:
        log(f"🔎 Verificando feed: {rss_url}")
        noticias_filtradas = filtrar_noticias(rss_url, links_ja_enviados)
        todas_as_novas_noticias.extend(noticias_filtradas)

    if not todas_as_novas_noticias:
        log("✅ Nenhuma notícia nova e relevante encontrada desta vez. Encerrando.")
    else:
        random.shuffle(todas_as_novas_noticias)
        enviadas_com_sucesso = 0
        total_a_enviar = len(todas_as_novas_noticias)
        log(f"📬 Total de {total_a_enviar} notícias para enviar. Iniciando disparos...")
        
        for noticia in todas_as_novas_noticias:
            mensagem = f"📰 {noticia['title']}\n\n🔗 {noticia['link']}"
            if enviar_telegram(mensagem):
                salvar_link_enviado(noticia['link'])
                enviadas_com_sucesso += 1

        log(f"✅ Tarefa concluída! {enviadas_com_sucesso} de {total_a_enviar} notícias foram enviadas.")

# === EXECUÇÃO PRINCIPAL ===
if __name__ == "__main__":
    executar_bot()
