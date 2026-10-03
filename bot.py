from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# NÃO VAZAR TOKEN!
TOKEN = "8345870648:AAHtBBwUz5BD6GI91_AhjxTYqFUCyIMXGCE"

# Ids dos grupos e tópicos do bot (Adquiridos ao usar /id)
grupo_suporte = -1004300089830
topico_notificacoes = 46
# Armazenar a relação entre tópico e o usuário
atendimentos = {}
# Tempo para notificar sobre o tópico fechado
tempo_notificacao = 3600  # 1 hora
# Tempo para deletar o tópico depois de fechado
tempo_deleteTopico = 86400  # 24 horas


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


# Notificar caso um tópico fique sem resposta
async def notificar_sem_resposta(context: ContextTypes.DEFAULT_TYPE):

    # Pega as informações que foram salvas quando o agendamento foi criado
    dados = context.job.data

    thread_id = dados["thread_id"]
    nome_topico = dados["nome_topico"]
    usuario_id = dados["usuario_id"]

    try:
        # Envia o aviso no tópico de notificações
        await context.bot.send_message(
            chat_id=grupo_suporte,
            message_thread_id=topico_notificacoes,
            text=(
                "⏰ SUPORTE AGUARDANDO RESPOSTA\n\n"
                f"📂 Tópico: {nome_topico}\n"
                f"🆔 ID do tópico: {thread_id}\n\n"
                "Este atendimento está aberto há um tempo "
                "e ainda não recebeu uma resposta.\n\n"
                "Verifique o tópico para decidir se é necessário "
                "responder ou se o atendimento já pode ser fechado."
            )
        )

        print(f"Notificação de falta de resposta enviada para {thread_id}.")

    except Exception as erro:
        print("Erro ao enviar notificação de falta de resposta:")
        print(erro)

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
        # Guarda qual usuário pertence a este atendimento
        atendimentos[thread_id] = {
        "usuario_id": usuario.id,
        "nome_topico": f"Suporte - {usuario.first_name}"
        }
        # Agenda a primeira verificação de falta de resposta
        context.job_queue.run_once(
        notificar_sem_resposta,
        when=tempo_notificacao,
        data={
        "thread_id": thread_id,
        "nome_topico": f"Suporte - {usuario.first_name}",
        "usuario_id": usuario.id
        },
        name=f"notificacao_{thread_id}"
        )
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


# /responder - Moderador responde ao usuário
async def responder_moderador(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # O moderador precisa usar o comando dentro de um tópico
    if update.message.message_thread_id is None:
        await update.message.reply_text(
            "Este comando precisa ser usado dentro de um tópico de suporte."
        )
        return

    thread_id = update.message.message_thread_id

    # Verifica se esse tópico está registrado como atendimento
    if thread_id not in atendimentos:
        await update.message.reply_text(
            "❌ Não encontrei o usuário associado a este tópico."
        )
        return

    # Junta tudo que foi escrito depois do /responder
    mensagem = " ".join(context.args)

    if not mensagem:
        await update.message.reply_text(
            "Use o comando assim:\n\n"
            "/responder Sua mensagem para o usuário"
        )
        return

    # Descobre qual usuário abriu esse atendimento
    usuario_id = atendimentos[thread_id]["usuario_id"]

    try:

        
        # Envia a resposta ao usuário
        await context.bot.send_message(
            chat_id=usuario_id,
            text=(
                "💬 RESPOSTA DO SUPORTE\n\n"
                f"{mensagem}\n\n"
                "Caso queira responder ao suporte, use:\n"
                "/responder Sua mensagem"
            )
        )

        # Reinicia o contador de falta de resposta
        # Procura a notificação que estava agendada para esse tópico
        jobs = context.job_queue.get_jobs_by_name(
            f"notificacao_{thread_id}"
        )

        # Cancela o agendamento anterior
        for job in jobs:
            job.schedule_removal()

        # Cria um novo contador
        # A partir daqui começa a contar novamente o tempo
        # definido em "tempo_notificacao".
        context.job_queue.run_once(
            notificar_sem_resposta,
            when=tempo_notificacao,
            data={
                "thread_id": thread_id,
                "nome_topico": f"Suporte - {update.effective_user.first_name}",
                "usuario_id": usuario_id
            },
            name=f"notificacao_{thread_id}"
        )

        # Confirma para o moderador
        await update.message.reply_text(
            "✅ Resposta enviada ao usuário!\n\n"
            "⏰ O contador de falta de resposta foi reiniciado."
        )

        print(f"Resposta enviada para o usuário {usuario_id}.")
        print(f"Contador do tópico {thread_id} reiniciado.")

    except Exception as erro:

        print("Erro ao enviar resposta ao usuário:")
        print(erro)

        await update.message.reply_text(
            "❌ Não foi possível enviar a resposta ao usuário."
        )


# /responder - Usuário responde ao suporte
async def responder_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):

    usuario = update.effective_user
    usuario_id = usuario.id

    mensagem = " ".join(context.args)

    if not mensagem:
        await update.message.reply_text(
            "Use o comando assim:\n\n"
            "/responder Sua mensagem"
        )
        return

    # Procura o atendimento desse usuário
    thread_id = None

    for id_topico, id_usuario in atendimentos.items():
        if id_usuario == usuario_id:
            thread_id = id_topico
            break

    if thread_id is None:
        await update.message.reply_text(
            "❌ Não encontrei um atendimento seu em aberto."
        )
        return

    try:

        # Envia a resposta do usuário para o tópico
        await context.bot.send_message(
            chat_id=grupo_suporte,
            message_thread_id=thread_id,
            text=(
                "👤 RESPOSTA DO USUÁRIO\n\n"
                f"{mensagem}"
            )
        )

        await update.message.reply_text(
            "✅ Sua resposta foi enviada para a equipe de suporte."
        )

        print(f"Resposta do usuário {usuario_id} enviada.")

    except Exception as erro:

        print("Erro ao enviar resposta do usuário:")
        print(erro)

        await update.message.reply_text(
            "❌ Não foi possível enviar sua resposta."
        )


# /responder - Decide se quem usou o comando foi o moderador ou o usuário
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    # Se veio do grupo de suporte e está dentro de um tópico
    # significa que quem tá respondendo é um moderador
    if (
        chat_id == grupo_suporte
        and update.message.message_thread_id is not None
    ):
        await responder_moderador(update, context)
        return

    # Se veio do privado do bot, significa que é o usuário respondendo ao suporte
    if chat_id > 0:
        await responder_usuario(update, context)
        return

    # Caso o comando seja usado em algum outro lugar
    await update.message.reply_text(
        "❌ O comando /responder só pode ser usado "
        "no atendimento ou no privado do bot."
    )
    
    
# Notificação de tópico fechado
async def notificar_topico_fechado(context: ContextTypes.DEFAULT_TYPE):

    dados = context.job.data

    chat_id = dados["chat_id"]
    thread_id = dados["thread_id"]
    nome_topico = dados["nome_topico"]

    try:
        await context.bot.send_message(
            chat_id=grupo_suporte,
            message_thread_id=topico_notificacoes,
            text=(
                "⏰ ATENÇÃO: TÓPICO FECHADO\n\n"
                f"📂 Tópico: {nome_topico}\n"
                f"🆔 ID do tópico: {thread_id}\n\n"
                "Este atendimento está fechado há 1 hora "
                "e ainda está aguardando tratamento.\n\n"
                "⚠️ O tópico será excluído automaticamente "
                "quando atingir o tempo configurado."
            )
        )

        print(f"Notificação enviada para o tópico {thread_id}.")

    except Exception as erro:
        print("Erro ao enviar notificação do tópico:")
        print(erro)
        
        
        
# Exclusão automática do tópico
async def excluir_topico(context: ContextTypes.DEFAULT_TYPE):

    dados = context.job.data

    chat_id = dados["chat_id"]
    thread_id = dados["thread_id"]
    nome_topico = dados["nome_topico"]

    try:
        # Notifica antes de excluir
        await context.bot.send_message(
            chat_id=grupo_suporte,
            message_thread_id=topico_notificacoes,
            text=(
                "🗑️ TÓPICO DE SUPORTE EXCLUÍDO\n\n"
                f"📂 Tópico: {nome_topico}\n"
                f"🆔 ID: {thread_id}\n\n"
                "O tópico atingiu o tempo máximo após ser fechado "
                "e foi excluído automaticamente."
            )
        )

        # Exclui o tópico
        await context.bot.delete_forum_topic(
            chat_id=chat_id,
            message_thread_id=thread_id
        )

        print(f"Tópico {thread_id} excluído automaticamente.")

    except Exception as erro:
        print("Erro ao excluir tópico:")
        print(erro)
        
        
# /fechar
async def fechar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.message_thread_id is None:
        await update.message.reply_text(
            "Este comando precisa ser usado dentro de um tópico."
        )
        return

    chat_id = update.effective_chat.id
    thread_id = update.message.message_thread_id

    try:
        # Fecha o tópico
        await context.bot.close_forum_topic(
            chat_id=chat_id,
            message_thread_id=thread_id
        )

        # Nome do tópico
        nome_topico = update.message.chat.title or "Suporte"

        # Dados que serão utilizados pelas tarefas agendadas
        dados_topico = {
            "chat_id": chat_id,
            "thread_id": thread_id,
            "nome_topico": nome_topico
        }

        # Agenda a notificação
        context.job_queue.run_once(
            notificar_topico_fechado,
            when=tempo_notificacao,
            data=dados_topico
        )

        # Agenda a exclusão
        context.job_queue.run_once(
            excluir_topico,
            when=tempo_deleteTopico,
            data=dados_topico
        )

        await update.message.reply_text(
            "🔒 Tópico fechado com sucesso!\n\n"
            "⏰ Uma notificação será enviada posteriormente "
            "caso o atendimento permaneça fechado.\n\n"
            "🗑️ O tópico também será excluído automaticamente "
            "após o tempo configurado."
        )

        print("Tópico fechado com sucesso!")
        print(f"ID do tópico: {thread_id}")

    except Exception as erro:
        # ⭐ NOVO: Verificar tipo de erro
        erro_str = str(erro)
        
        if "Topic_not_modified" in erro_str:
            await update.message.reply_text(
                "⚠️ Este tópico já está fechado ou não pode ser fechado."
            )
            print(f"Tópico {thread_id} já estava fechado.")
        
        elif "BadRequest" in erro_str or "Forbidden" in erro_str:
            await update.message.reply_text(
                "❌ O bot não tem permissão para fechar tópicos.\n"
                "Certifique-se de que o bot é admin do grupo."
            )
            print(f"Erro de permissão ao fechar tópico {thread_id}")
        
        else:
            await update.message.reply_text(
                "❌ Não foi possível fechar o tópico."
            )
            print(f"Erro ao fechar tópico: {erro}")


# /excluir
async def excluir(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.message_thread_id is None:
        await update.message.reply_text(
            "Este comando precisa ser usado dentro de um tópico."
        )
        return

    chat_id = update.effective_chat.id
    thread_id = update.message.message_thread_id

    try:
        # ⭐ NOVO: Procurar o nome do tópico no dicionário
        nome_topico = None
        for tid, dados in atendimentos.items():
            if tid == thread_id and isinstance(dados, dict):
                nome_topico = dados.get("nome_topico", f"Tópico {thread_id}")
                break
        
        # Se não encontrar, usar valor padrão
        if nome_topico is None:
            nome_topico = f"Suporte - Tópico {thread_id}"

        # Deletar tópico
        await context.bot.delete_forum_topic(
            chat_id=chat_id,
            message_thread_id=thread_id
        )

        # Notifica no tópico de notificações
        await context.bot.send_message(
            chat_id=grupo_suporte,
            message_thread_id=topico_notificacoes,
            text=(
                "🗑️ TÓPICO DE SUPORTE EXCLUÍDO\n\n"
                f"📂 Tópico: {nome_topico}\n"  # ⭐ CORRETO
                f"🆔 ID: {thread_id}\n\n"
                "O tópico foi excluído manualmente."
            )
        )

        await update.message.reply_text(
            "🗑️ Tópico excluído com sucesso!"
        )

        print(f"Tópico '{nome_topico}' (ID: {thread_id}) excluído manualmente.")

    except Exception as erro:
        erro_str = str(erro)
        
        if "Topic_not_found" in erro_str or "BadRequest" in erro_str:
            await update.message.reply_text(
                "❌ Tópico não encontrado ou já foi excluído."
            )
        else:
            await update.message.reply_text(
                "❌ Não foi possível excluir o tópico."
            )
        
        print(f"Erro ao excluir tópico: {erro}")
        

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
app.add_handler(CommandHandler("responder", responder))
app.add_handler(CommandHandler("id", id_grupo))
app.add_handler(CommandHandler("fechar", fechar))
app.add_handler(CommandHandler("excluir", excluir))

print("Bot iniciado!")

app.run_polling()