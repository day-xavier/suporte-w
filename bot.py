from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8345870648:AAHtBBwUz5BD6GI91_AhjxTYqFUCyIMXGCE"
moderador_suporte = 1489350052

# Função Assíncrona para lidar com o comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("oi")
    await update.message.reply_text(

"""Olá! Seja bem-vindo ao suporte!

Como posso te ajudar?
Caso esteja enfrentando algum problema ou tenha encontrado algum erro, utilize o comando /reportar para relatar o ocorrido.
        
Ao relatar um problema, tente explicar com o máximo de detalhes possível para que possamos te ajudar melhor.
Obrigado por entrar em contato!"""

        )

async def reportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user
    mensagem_usuario = " ".join(context.args)
    await update.message.reply_text("Sua solicitação foi enviada para a nossa equipe de suporte! Aguarde nosso retorno.")

    texto_notificacao = (
        f"NOVO PEDIDO DE SUPORTE\n\n"
        f"Usuário: {usuario.first_name} (@{usuario.username})\n"
        f"Mensagem: {mensagem_usuario}"
        )
    # O bot envia a mensagem diretamente para o canal/chat do moderador
    await context.bot.send_message(
        chat_id=moderador_suporte,
        text=texto_notificacao) 



app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reportar", reportar))

app.run_polling()