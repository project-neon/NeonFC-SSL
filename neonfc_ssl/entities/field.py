class Field(object):
    def __init__(self):
        self.current_data = []

        self.fieldLength = 0
        self.fieldWidth = 0
        self.goalWidth = 0
        self.leftGoalLine = [0, 0]
        self.rightGoalLine = [0, 0]
        self.halfwayLine = [0, 0]
        self.leftArea = [0, 0]
        self.rightArea = [0, 0]
        self.rightFirstPost = [0, 0]
        self.leftFirstPost = [0, 0]

    def _update_geometry(self):
        self.fieldLength = self.current_data.get('fieldLength')
        self.fieldWidth = self.current_data.get('fieldWidth')
        self.goalWidth = self.current_data.get('goalWidth')

        self.leftGoalLine = [self.current_data.get('fieldLines').get('LeftGoalLine').get('p1').get('x'),
                             self.current_data.get('fieldLines').get('LeftGoalLine').get('p1').get('y')]
        
        self.rightGoalLine = [self.current_data.get('fieldLines').get('RightGoalLine').get('p1').get('x'),
                              self.current_data.get('fieldLines').get('RightGoalLine').get('p1').get('y')]
        
        self.halfwayLine = [self.current_data.get('fieldLines').get('HalfwayLine').get('p1').get('x'),
                            self.current_data.get('fieldLines').get('HalfwayLine').get('p1').get('y')]
        
        self.leftArea = [self.current_data.get('fieldLines').get('LeftPenaltyStretch').get('p1').get('x'),
                         self.current_data.get('fieldLines').get('LeftPenaltyStretch').get('p1').get('y')]
        
        self.rightArea = [self.current_data.get('fieldLines').get('RightPenaltyStretch').get('p1').get('x'),
                          self.current_data.get('fieldLines').get('RightPenaltyStretch').get('p1').get('y')]
        
        self.rightFirstPost = [self.current_data.get('fieldLines').get('RightGoalBottomLine').get('p1').get('x'),
                               self.current_data.get('fieldLines').get('RightGoalBottomLine').get('p1').get('y')
                               ]
        self.leftFirstPost = [self.current_data.get('fieldLines').get('LeftGoalBottomLine').get('p1').get('x'), 
                              self.current_data.get('fieldLines').get('LeftGoalBottomLine').get('p1').get('y')]
        
        print(f"x: {self.leftFirstPost[0]}, y:{self.leftGoalLine[1]}")


    def update(self, frame):
        self.current_data = frame
        if self.current_data is not None:
            self._update_geometry()

        #print(f"{self.current_data}\n\n")
    