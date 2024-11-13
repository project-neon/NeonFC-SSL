from dataclasses import dataclass


@dataclass
class Field:
    fieldLength: int = 9
    fieldWidth: int = 6
    penaltyAreaDepth: int = 0
    penaltyAreaWidth: int = 0
    goalWidth: int = 0
    leftGoalLine: tuple[int, int] = tuple((0, 0))
    rightGoalLine: tuple[int, int] = tuple((0, 0))
    halfwayLine: tuple[int, int] = tuple((0, 0))
    leftArea: tuple[int, int] = tuple((0, 0))
    rightArea: tuple[int, int] = tuple((0, 0))
    rightFirstPost: tuple[int, int] = tuple((0, 0))
    leftFirstPost: tuple[int, int] = tuple((0, 0))

    initialized: bool = False

    def update(self, frame):
        if frame is None:
            return
        
        self.fieldLength = frame.get('fieldLength')
        self.fieldWidth = frame.get('fieldWidth')
        self.goalWidth = frame.get('goalWidth')
        self.penaltyAreaDepth = frame.get('penaltyAreaDepth')  # nao tem no grsim, usar leftpenaltyscretch
        self.penaltyAreaWidth = frame.get('penaltyAreaWidth')  # idem
        
        self.leftGoalLine = (
            frame.get('fieldLines').get('LeftGoalLine').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('LeftGoalLine').get('p1').get('y') + .5 * self.fieldWidth
        )

        self.rightGoalLine = (
            frame.get('fieldLines').get('RightGoalLine').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('RightGoalLine').get('p1').get('y') + .5 * self.fieldWidth
        )
        
        self.halfwayLine = (
            frame.get('fieldLines').get('HalfwayLine').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('HalfwayLine').get('p1').get('y') + .5 * self.fieldWidth
        )
        
        self.leftArea = (
            frame.get('fieldLines').get('LeftPenaltyStretch').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('LeftPenaltyStretch').get('p1').get('y') + .5 * self.fieldWidth
        )
        
        self.rightArea = (
            frame.get('fieldLines').get('RightPenaltyStretch').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('RightPenaltyStretch').get('p1').get('y') + .5 * self.fieldWidth
        )
        
        self.rightFirstPost = (
            frame.get('fieldLines').get('RightGoalBottomLine').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('RightGoalBottomLine').get('p1').get('y') + .5 * self.fieldWidth
        )

        self.leftFirstPost = (
            frame.get('fieldLines').get('LeftGoalBottomLine').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('LeftGoalBottomLine').get('p1').get('y') + .5 * self.fieldWidth
        )

        self.leftPenaltyStretch = (
            frame.get('fieldLines').get('LeftPenaltyStretch').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('LeftPenaltyStretch').get('p1').get('y') + .5 * self.fieldWidth
        )

        self.rightPenaltyStretch = (
            frame.get('fieldLines').get('RightPenaltyStretch').get('p1').get('x') + .5 * self.fieldLength,
            frame.get('fieldLines').get('RightPenaltyStretch').get('p1').get('y') + .5 * self.fieldWidth
        )

        self.initialized = True
