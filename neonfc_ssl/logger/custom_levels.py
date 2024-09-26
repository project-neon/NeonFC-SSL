import logging

# Adds two extra logging levels

# Game Level is the lowest represents game events that the NeonFC caught
GAME_LVL_NUM = 6
# Decision Level is above represent decisions made based on the received information
DECISION_LVL_NUM = 7

logging.addLevelName(GAME_LVL_NUM, "GAME")
logging.addLevelName(DECISION_LVL_NUM, "DECISION")


def game(self, message, *args, **kws):
    if self.isEnabledFor(GAME_LVL_NUM):
        # Yes, logger takes its '*args' as 'args'.
        self._log(GAME_LVL_NUM, message, args, **kws)


def decision(self, message, *args, **kws):
    if self.isEnabledFor(DECISION_LVL_NUM):
        # Yes, logger takes its '*args' as 'args'.
        self._log(DECISION_LVL_NUM, message, args, **kws)


logging.Logger.game = game
logging.Logger.decision = decision

