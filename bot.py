from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# NÃO VAZAR TOKEN!
TOKEN = "8345870648:AAHtBBwUz5BD6GI91_AhjxTYqFUCyIMXGCE"

# Ids dos grupos e tópicos do bot (Adquiridos ao usar /id)
grupo_suporte = -1004300089830
topico_notificacoes = 46



# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Comando /start recebido")

    await update.message.reply_text(
        """🔮 Olá! Seja bem-vindo ao mágico suporte!

Como podemos te ajudar?

Caso esteja enfrentando algum problema, tenha encontrado algum erro, queira fazer uma sugestão ou realizar uma denúncia, utilize o comando /reportar para relatar o ocorrido.

Ao relatar um problema, tente explicar a situação com o máximo de detalhes possível, para que possamos te ajudar da melhor forma.

Agradecemos por entrar em contato! 💚
Esperamos que você tenha uma ótima jornada em nosso bot. 🪄✨"""
    )



# /reportar
async def reportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user
    mensagem_usuario = " ".join(context.args)

    # Confirma para o usuário
    await update.message.reply_text(
        "✅ Sua solicitação foi recebida!\n"
        "Nossa equipe de suporte irá analisar e responder em breve."
    )

    try:
        # Cria o tópico do atendimento
        topico = await context.bot.create_forum_topic(
            chat_id=grupo_suporte,
            name=f"Suporte - {usuario.first_name}"
        )

        thread_id = topico.message_thread_id

        # Mensagem dentro do tópico do atendimento
        texto_atendimento = (
            "🎫 NOVO PEDIDO DE SUPORTE\n\n"
            f"👤 Usuário: {usuario.first_name}\n"
            f"🔹 Username: @{usuario.username or 'sem username'}\n"
            f"🆔 ID: {usuario.id}\n"
            f"💬 Mensagem: {mensagem_usuario}"
        )

        await context.bot.send_message(
            chat_id=grupo_suporte,
            message_thread_id=thread_id,
            text=texto_atendimento
        )

        # Notificação no tópico de notificações
        await context.bot.send_message(
            chat_id=grupo_suporte,
            message_thread_id=topico_notificacoes,
            text=(
                "🔔 NOVO SUPORTE ABERTO!\n\n"
                f"👤 Usuário: {usuario.first_name}\n"
                f"💬 Mensagem: {mensagem_usuario}\n\n"
                f"📂 Tópico: Suporte - {usuario.first_name}"
            )
        )

        print("Suporte criado com sucesso!")
        print(f"Tópico do suporte: {thread_id}")
        print(f"Tópico de notificações: {topico_notificacoes}")

    except Exception as erro:
        print("ERRO AO PROCESSAR SUPORTE:")
        print(erro)



# /fechar
async def fechar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.message_thread_id is None:
        await update.message.reply_text(
            "Este comando precisa ser usado dentro de um tópico."
        )
        return

    try:
        await context.bot.close_forum_topic(
            chat_id=update.effective_chat.id,
            message_thread_id=update.message.message_thread_id
        )

        print("Tópico fechado com sucesso!")

    except Exception as erro:
        print("Erro ao fechar tópico:")
        print(erro)

        await update.message.reply_text(
            "Não foi possível fechar o tópico."
        )



# /id
async def id_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"ID do grupo: {update.effective_chat.id}\n"
        f"ID do tópico: {update.message.message_thread_id}"
    )


# INICIALIZAÇÃO DO BOT
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reportar", reportar))
app.add_handler(CommandHandler("id", id_grupo))
app.add_handler(CommandHandler("fechar", fechar))

print("Bot iniciado!")

app.run_polling()