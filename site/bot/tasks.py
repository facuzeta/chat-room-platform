import asyncio
import logging
import random

from celery import shared_task
from channels.layers import get_channel_layer

from group_manager.services import get_stage_and_change, store_bot_chat

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=None)
def celery_run_bot(self, data):
    from group_manager.models import Participant

    pk = data.get("pk")
    logger.info("Running bot for participant %s", pk)

    bot_participant = Participant.objects.get(id=pk)
    bot_current_stage = get_stage_and_change(bot_participant)
    group = bot_participant.group
    channel_layer = get_channel_layer()

    if group is None:
        return

    if bot_current_stage.name == "s1":
        logger.info("Bot %s waiting for participants to finish s1", pk)
        self.retry(args=[data], countdown=10, throw=False)
        return

    total_questions = group.experiment.get_total_questions()
    s2_stages = [f"s2_{i}" for i in range(1, total_questions + 1)]

    if bot_current_stage.name in s2_stages:
        if bot_participant.bot.reply_probability > random.uniform(0, 1):
            logger.info("Bot %s sending response", pk)
            context, bot_response = bot_participant.message_bot()
            logger.info("Bot %s got response: %s", pk, bot_response)

            stage_after_think = get_stage_and_change(bot_participant)
            if (
                bot_current_stage == stage_after_think
                and bot_response
                and bot_response != "<EMPTY/>"
            ):
                store_bot_chat(bot_participant, bot_current_stage, bot_response, context)
                try:
                    asyncio.run(
                        channel_layer.group_send(
                            f"chat_{group.name}",
                            {
                                "type": "chat_message",
                                "message": bot_response,
                                "user": bot_participant.nickname,
                                "color": bot_participant.get_color(),
                                "user_id": bot_participant.bot.id,
                                "is_bot": True,
                            },
                        )
                    )
                except Exception:
                    logger.exception("Failed to send bot message to WebSocket")
        else:
            logger.info("Bot %s skipped (reply probability)", pk)

        self.retry(args=[data], countdown=bot_participant.bot.poll_time, throw=False)
    else:
        get_stage_and_change(bot_participant)
