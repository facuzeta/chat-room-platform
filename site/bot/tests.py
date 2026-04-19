from django.test import TestCase
from django.contrib.auth import get_user_model
from bot.models import Bot, all_participants_talked
from group_manager.models import (
    Participant, Group, Experiment, Stage, StageParticipant,
    StageTimes, Question, Chat,
)

User = get_user_model()


class AllParticipantsTalkedTests(TestCase):
    """Pure logic tests for all_participants_talked — no DB needed."""

    def _participant(self, pk):
        p = object.__new__(Participant)
        p.pk = pk
        return p

    def test_empty_history_returns_true(self):
        self.assertTrue(all_participants_talked([], [self._participant(1)]))

    def test_no_assistant_message_returns_true(self):
        # Bug fix: bot should be allowed to send the first message
        p = self._participant(1)
        history = [{"role": "user", "content": "hi", "participant": p}]
        self.assertTrue(all_participants_talked(history, [p]))

    def test_all_participants_talked_after_bot(self):
        p1, p2 = self._participant(1), self._participant(2)
        history = [
            {"role": "assistant", "content": "hello", "participant": None},
            {"role": "user", "content": "msg", "participant": p1},
            {"role": "user", "content": "msg", "participant": p2},
        ]
        self.assertTrue(all_participants_talked(history, [p1, p2]))

    def test_not_all_participants_talked_after_bot(self):
        p1, p2 = self._participant(1), self._participant(2)
        history = [
            {"role": "assistant", "content": "hello", "participant": None},
            {"role": "user", "content": "msg", "participant": p1},
        ]
        self.assertFalse(all_participants_talked(history, [p1, p2]))

    def test_only_checks_since_last_bot_message(self):
        p1, p2 = self._participant(1), self._participant(2)
        history = [
            {"role": "user", "content": "msg", "participant": p1},
            {"role": "user", "content": "msg", "participant": p2},
            {"role": "assistant", "content": "reply", "participant": None},
            {"role": "user", "content": "msg", "participant": p1},
            {"role": "assistant", "content": "reply", "participant": None},
            # p2 has not talked since last assistant message
        ]
        self.assertFalse(all_participants_talked(history, [p1, p2]))


class BotSendMessageTests(TestCase):

    def setUp(self):
        self.experiment = Experiment.objects.create(
            name="Test Experiment",
            stage_names="ws1 s1 s2_1 s3 thanks",
        )
        for name in ["ws1", "s1", "s2_1", "s3", "thanks"]:
            stage = Stage.objects.create(name=name, label=name)
            StageTimes.objects.create(stage=stage, experiment=self.experiment, timeout_in_seconds=300)

        self.question = Question.objects.create(text="What do you think?", experiment=self.experiment)
        self.group = Group.objects.create(
            name="test_group",
            experiment=self.experiment,
            question_order_s2=[{"question_id": self.question.id, "text": self.question.text}],
        )

        self.user = User.objects.create_user(username="human1", password="pass")
        self.human = Participant.objects.create(user=self.user, group=self.group, nickname="Human1")
        StageParticipant.objects.create(participant=self.human, stage=Stage.objects.get(name="s2_1"))

        self.bot_model = Bot.objects.create(
            behaviour_nickname="TestBot",
            chatroom_nickname="Bot",
            model="mockup_hello",
            system_prompt="Be helpful.",
            wait_reply_to_generate_again=False,
            use_time_left_threshold=False,
            send_message_if_chat_inactive=False,
        )
        self.bot_participant = Participant.objects.create(bot=self.bot_model, group=self.group, nickname="Bot")
        StageParticipant.objects.create(participant=self.bot_participant, stage=Stage.objects.get(name="s2_1"))

    def test_mockup_hello_returns_hello(self):
        _, response = self.bot_model.send_message(self.bot_participant)
        self.assertEqual(response, "hello")

    def test_mockup_repeat_with_no_history_returns_hello(self):
        self.bot_model.model = "mockup_repeat"
        self.bot_model.save()
        _, response = self.bot_model.send_message(self.bot_participant)
        self.assertEqual(response, "hello")

    def test_mockup_repeat_echoes_last_message(self):
        self.bot_model.model = "mockup_repeat"
        self.bot_model.save()
        stage = Stage.objects.get(name="s2_1")
        Chat.objects.create(text="Test message", participant=self.human, stage=stage)
        _, response = self.bot_model.send_message(self.bot_participant)
        self.assertEqual(response, "Human1:Test message")

    def test_wait_reply_allows_first_message(self):
        # With empty chat (bot hasn't spoken yet), the bot should speak freely
        self.bot_model.wait_reply_to_generate_again = True
        self.bot_model.save()
        _, response = self.bot_model.send_message(self.bot_participant)
        self.assertEqual(response, "hello")

    def test_wait_reply_blocks_before_human_responds(self):
        self.bot_model.wait_reply_to_generate_again = True
        self.bot_model.save()
        stage = Stage.objects.get(name="s2_1")
        Chat.objects.create(text="Bot message", participant=self.bot_participant, stage=stage)
        _, response = self.bot_model.send_message(self.bot_participant)
        self.assertEqual(response, "")

    def test_wait_reply_allows_after_everyone_responded(self):
        self.bot_model.wait_reply_to_generate_again = True
        self.bot_model.save()
        stage = Stage.objects.get(name="s2_1")
        Chat.objects.create(text="Bot message", participant=self.bot_participant, stage=stage)
        Chat.objects.create(text="Human reply", participant=self.human, stage=stage)
        _, response = self.bot_model.send_message(self.bot_participant)
        self.assertEqual(response, "hello")
