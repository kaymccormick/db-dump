from unittest import TestCase
from unittest.mock import MagicMock

from db_dump.args import OptionAction


class TestOptionAction(TestCase):
    def test___call__(self):
        action = OptionAction(["--option"], "option")
        mock = MagicMock()
        mock2 = MagicMock()
        action(mock, mock2, 'x=y')
        print(mock2.)



