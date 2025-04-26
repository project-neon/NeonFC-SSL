import logging

# Adds two extra logging levels

# Game Level is the lowest represents game events that the NeonFC caught
TRACKING = 6
# Decision Level is above represent decisions made based on the received information
DECISION = 7

LEVELS = {TRACKING, DECISION}

logging.addLevelName(TRACKING, "TRACKING")
logging.addLevelName(DECISION, "DECISION")


def tracking(self, message, *args, **kws):
    if self.isEnabledFor(TRACKING):
        # Yes, logger takes its '*args' as 'args'.
        self._log(TRACKING, message, args, **kws)


def decision(self, message, *args, **kws):
    if self.isEnabledFor(DECISION):
        # Yes, logger takes its '*args' as 'args'.
        self._log(DECISION, message, args, **kws)


logging.Logger.tracking = tracking
logging.Logger.decision = decision

