import pytest

from handlers.help import HelpCommandHandler


class TestHelpCommandHandler:
    @pytest.mark.asyncio
    async def test_handler_send_answer(self, message):
        await HelpCommandHandler(message).handle()

        assert len(message.answers) == 1

    @pytest.mark.parametrize(
        "providers, expected_result",
        [
            ((), "We do not support any banks yet."),
            (("BankA",), "We support BankA."),
            (("BankA", "BankB"), "We support BankA and BankB."),
            (("BankA", "BankB", "BankC"), "We support BankA, BankB and BankC."),
        ],
    )
    def test_get_supported_banks(self, providers, expected_result):
        assert HelpCommandHandler._get_supported_banks(providers) == expected_result
