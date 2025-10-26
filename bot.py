callback_query
    await q.answer()
    _, cur, days = q.data.split(":")  # buy:RUB:7  /  buy:USD:30

    if TEST_MODE:
        return await q.message.reply_text(
            "⚠️ Платежи пока в тестовом режиме. Как только ЮKassa/провайдер одобрят — кнопки заработают. "
            "Напомни мне, и я пришлю ссылку в канал вручную 🙌"
        )

    if cur == "RUB":
        if not YOOKASSA_PROVIDER_TOKEN:
            return await q.message.reply_text("Платежи в RUB сейчас недоступны. Попробуй позже.")
        if days == "7":
            title, amount, payload = "Доступ на 7 дней", RUB_7, "order:rub:7"
        else:
            title, amount, payload = "Доступ на 30 дней", RUB_30, "order:rub:30"

        await q.message.reply_invoice(
            title=title,
            description="Оплата через Telegram Payments (YooKassa).",
            provider_token=YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=rub(amount),
            payload=payload,
            need_name=False,
            is_flexible=False,
            start_parameter="ann_access_rub"
        )

    else:  # USD
        if not USD_PROVIDER_TOKEN:
            return await q.message.reply_text("Платежи в USD сейчас недоступны. Выбери оплату в RUB.")
        if days == "7":
            title, amount, payload = "Access for 7 days", USD_7, "order:usd:7"
        else:
            title, amount, payload = "Access for 30 days", USD_30, "order:usd:30"

        await q.message.reply_invoice(
            title=title,
            description="Payment via Telegram Payments.",
            provider_token=USD_PROVIDER_TOKEN,
            currency="USD",
            prices=usd(amount),
            payload=payload,
            need_name=False,
            is_flexible=False,
            start_parameter="ann_access_usd"
        )

async def on_precheckout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # тут можно валидировать payload, суммы и т.п.
    await update.pre_checkout_query.answer(ok=True)

async def on_success(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sp = update.message.successful_payment
    payload = sp.invoice_payload
    log.info("SUCCESS payment: %s | %s %s", payload, sp.total_amount, sp.currency)

    # выдаём одноразовую ссылку в канал
    try:
        invite = await ctx.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            expire_date=int(time.time()) + INVITE_TTL_SEC,
            member_limit=1
        )
        await update.message.reply_text(
            "✅ Оплата прошла!\n"
            f"Ваша ссылка в закрытый канал (активна {INVITE_TTL_SEC//60} мин, одноразовая):\n"
            f"{invite.invite_link}"
        )
    except Exception as e:
        log.exception("Invite error: %s", e)
        await update.message.reply_text(
            "✅ Оплата прошла, но не удалось выдать ссылку автоматически. "
            "Напишите сюда, всё решим."
        )

def build_app() -> Application:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CallbackQueryHandler(on_currency_choice, pattern=r"^cur:"))
    app.add_handler(CallbackQueryHandler(on_back_main, pattern=r"^back:main$"))
    app.add_handler(CallbackQueryHandler(on_buy, pattern=r"^buy:"))
    app.add_handler(PreCheckoutQueryHandler(on_precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, on_success))
    return app

if name == "__main__":
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is empty. Set env var BOT_TOKEN.")
    if CHANNEL_ID == 0:
        log.warning("CHANNEL_ID not set. Invite link will fail until you set CHANNEL_ID and give bot admin rights.")
    build_app().run_polling()
