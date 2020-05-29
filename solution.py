import random
import sys


class Solution:
    def __init__(self, shapeCoords, length, width):
        self.shapeCoords = shapeCoords
        self.length = length
        self.width = width
        self.lengthFitness = 0
        self.widthFitness = 0


class SolutionGenerator:
    def __init__(self, problemSpecs):
        self.problemSpecs = problemSpecs
        self.problemSpecs["maxSheetLength"] = self._calcMaxSheetLength()

    def _calcMaxSheetLength(self):
        length = 0
        for shape in self.problemSpecs["shapeInfo"]:
            length += self._getShapeLargestSide(shape)
        return length

    def _getShapeLargestSide(self, shape):
        vertices = self._getShapeVertices(shape)
        horizontalLength = abs(vertices[0][0] - vertices[1][0]) + 1
        verticalLength = abs(vertices[0][1] - vertices[2][1]) + 1

        return max(horizontalLength, verticalLength)

    def _getShapeVertices(self, shape):
        # Find the vertices of the smallest rectangle that can enclose the shape.
        vertices = [[0, 0], [0, 0], [0, 0], [0, 0]]
        currPos = [0, 0]
        for step in shape:
            direction = step[0]
            paces = int(step[1:])

            if direction == "D":
                currPos[1] -= paces
                if currPos[1] < vertices[2][1]:
                    vertices[2][1] = currPos[1]
                    vertices[3][1] = currPos[1]
            elif direction == "R":
                currPos[0] += paces
                if currPos[0] > vertices[1][0]:
                    vertices[1][0] = currPos[0]
                    vertices[3][0] = currPos[0]
            elif direction == "U":
                currPos[1] += paces
                if currPos[1] > vertices[0][1]:
                    vertices[0][1] = currPos[1]
                    vertices[1][1] = currPos[1]
            elif direction == "L":
                currPos[0] -= paces
                if currPos[0] < vertices[0][0]:
                    vertices[0][0] = currPos[0]
                    vertices[2][0] = currPos[0]
        return vertices

    def getRandomSolution(self):
        grid = [[0] * self.problemSpecs["sheetWidth"] for i in range(self.problemSpecs["maxSheetLength"])]
        coordList = []
        for shape in self.problemSpecs["shapeInfo"]:
            coords = self._getRandomCoordsConstrained()
            while not self._coordsAreValid(grid, shape, coords):
                coords = self._getRandomCoordsConstrained()
            grid = self._addShapeToGrid(shape, grid, coords)

            coordList.append(coords)
        dimensions = self.getSheetDimensionsConstrained(coordList)
        length = dimensions[1] + 1
        width = dimensions[3] + 1
        solution = Solution(coordList, length, width)
        solution.lengthFitness = self.problemSpecs["maxSheetLength"] - length
        solution.widthFitness = self.problemSpecs["sheetWidth"] - width
        return solution

    def _getRandomCoordsConstrained(self):
        coords = []
        coords.append(random.randint(0, self.problemSpecs["maxSheetLength"] - 1))
        coords.append(random.randint(0, self.problemSpecs["sheetWidth"] - 1))
        coords.append(random.randint(0, 3))
        return coords

    def _coordsAreValid(self, grid, shape, coords):
        position = [coords[0], coords[1]]
        if grid[position[0]][position[1]] == 1:
            return False

        moveDict = {
            "L": [-1, 0],
            "R": [1, 0],
            "U": [0, 1],
            "D": [0, -1]
        }
        rotatedShape = self._rotateShape(shape, coords[2])
        for step in rotatedShape:
            moveVect = moveDict[step[0]]
            paces = int(step[1:])
            for pace in range(paces):
                position[0] += moveVect[0]
                position[1] += moveVect[1]
                if position[0] > len(grid) - 1 or position[0] < 0:
                    return False
                if position[1] > len(grid[0]) - 1 or position[1] < 0:
                    return False
                if grid[position[0]][position[1]] == 1:
                    return False

        return True

    def _rotateShape(self, shape, rotation):
        # Map the shape's steps to their rotated counterparts
        if rotation == 0:
            return shape

        # Create the mapping from normal orientation to each 90 degree rotation.
        rotationMap = {}
        rotationMap[1] = {
            "R": "D",
            "U": "R",
            "L": "U",
            "D": "L",
        }
        rotationMap[2] = {
            "R": "L",
            "U": "D",
            "L": "R",
            "D": "U",
        }
        rotationMap[3] = {
            "R": "U",
            "U": "L",
            "L": "D",
            "D": "R",
        }

        # Change the direction char in the step according to the rotation
        rotateDict = rotationMap[rotation]
        rotatedStepList = []
        for step in shape:
            direction = step[0]
            dirRotated = rotateDict[direction]
            newStep = dirRotated + step[1:]
            rotatedStepList.append(newStep)
        return rotatedStepList

    def _addShapeToGrid(self, shape, grid, coords):
        position = [coords[0], coords[1]]
        grid[position[0]][position[1]] = 1
        moveDict = {
            "L": [-1, 0],
            "R": [1, 0],
            "U": [0, 1],
            "D": [0, -1]
        }
        rotatedShape = self._rotateShape(shape, coords[2])
        for step in rotatedShape:
            moveVect = moveDict[step[0]]
            paces = int(step[1:])
            for pace in range(paces):
                position[0] += moveVect[0]
                position[1] += moveVect[1]
                grid[position[0]][position[1]] = 1

        return grid

    def _drawShape(self, shape, coords):
        squareList = []
        position = [coords[0], coords[1]]
        squareList.append(position.copy())
        moveDict = {
            "L": [-1, 0],
            "R": [1, 0],
            "U": [0, 1],
            "D": [0, -1]
        }
        rotatedShape = self._rotateShape(shape, coords[2])
        for step in rotatedShape:
            moveVect = moveDict[step[0]]
            paces = int(step[1:])
            for pace in range(paces):
                position[0] += moveVect[0]
                position[1] += moveVect[1]
                squareList.append(position.copy())
        return squareList

    def addMutations(self, solution):
        validSolution = []
        for geneNum in range(len(solution)):
            validSolution = self.addNewGene(geneNum, solution[geneNum], validSolution.copy())

        return validSolution

    def addNewGene(self, shapeNum, gene, solution):
        gene = [0, 0, 0]
        if not gene:
            gene = self._getRandomCoordsConstrained()

        grid = []
        for shape in range(len(solution)):
            squares = self._drawShape(self.problemSpecs["shapeInfo"][shape], solution[shape])
            grid += squares

        geneFound = False
        while not geneFound:
            checkSquares = self._drawShape(self.problemSpecs["shapeInfo"][shapeNum], gene)
            invalid = False
            for square in checkSquares:
                yOutOfBounds = (square[0] < 0) or (square[0] > self.problemSpecs["maxSheetLength"] - 1)
                xOutOfBounds = (square[1] < 0) or (square[1] > self.problemSpecs["sheetWidth"] - 1)
                if square in grid or xOutOfBounds or yOutOfBounds:
                    invalid = True
                    break
            if not invalid:
                geneFound = True
            else:
                gene = self._getRandomCoordsConstrained()

        solution.append(gene)
        return solution

    def solutionIsValid(self, solution):
        squares = []
        for coord in range(len(solution)):
            checkSquares = self._drawShape(self.problemSpecs["shapeInfo"][coord], solution[coord])
            for square in checkSquares:
                yOutOfBounds = (square[0] < 0) or (square[0] > self.problemSpecs["maxSheetLength"] - 1)
                xOutOfBounds = (square[1] < 0) or (square[1] > self.problemSpecs["sheetWidth"] - 1)
                if square in squares or xOutOfBounds or yOutOfBounds:
                    print("Seeded solution was invalid, discarding...")
                    return False
            squares += checkSquares
        return True

    def getSheetDimensionsConstrained(self, solution):
        filledSquares = []
        for coord in range(len(solution)):
            filledSquares += self._drawShape(self.problemSpecs["shapeInfo"][coord], solution[coord])

        lowX = 0
        lowY = 0
        highX = max(l[0] for l in solution)
        highY = max(l[1] for l in solution)
        return [lowX, highX, lowY, highY]


class SolutionTracker:
    def __init__(self):
        self.averageLengthFitnessRecords = []
        self.averageWidthFitnessRecords = []
        self.bestLengthFitnessRecords = []
        self.bestWidthFitnessRecords = []
        self.bestFront = []
        self.frontChangeRecords = []

    def addGeneration(self, population):
        lengthFitnessArr = [solution.lengthFitness for solution in population]
        widthFitnessArr = [solution.widthFitness for solution in population]

        genLengthMax = max(lengthFitnessArr)
        genLengthMaxIndex = lengthFitnessArr.index(genLengthMax)
        genWidthMax = max(widthFitnessArr)
        genWidthMaxIndex = widthFitnessArr.index(genWidthMax)

        genLengthAvg = sum(lengthFitnessArr) / len(lengthFitnessArr)
        genWidthAvg = sum(widthFitnessArr) / len(widthFitnessArr)

        self.averageLengthFitnessRecords.append(genLengthAvg)
        self.bestLengthFitnessRecords.append(genLengthMax)
        self.averageWidthFitnessRecords.append(genWidthAvg)
        self.bestWidthFitnessRecords.append(genWidthMax)

        currFront = self.getLevels(population)[0]
        frontSolutions = [population[i] for i in currFront]
        if not self.bestFront:
            self.bestFront = frontSolutions
        else:
            proportions = self.getFrontDominanceProportions(frontSolutions, self.bestFront)
            if proportions[0] > proportions[1]:
                self.bestFront = frontSolutions
                self.frontChangeRecords.append(1)
            else:
                self.frontChangeRecords.append(0)

    def getLevels(self, population):
        levels = []

        for solution in range(len(population)):
            if not levels:
                levels.append([solution])
                continue

            levelFound = False
            level = 0
            while not levelFound:
                if level > len(levels) - 1:
                    levels.append([solution])
                    break

                toRemove = []
                dominated = []
                levelValid = True
                levelCheck = levels[level]
                for check in range(len(levelCheck)):
                    if population[levelCheck[check]].lengthFitness > population[solution].lengthFitness:
                        if population[levelCheck[check]].widthFitness >= population[solution].widthFitness:
                            levelValid = False
                            break
                        else:
                            continue
                    if population[levelCheck[check]].widthFitness > population[solution].widthFitness:
                        if population[levelCheck[check]].lengthFitness >= population[solution].lengthFitness:
                            levelValid = False
                            break
                        else:
                            continue
                    if population[levelCheck[check]].lengthFitness == population[solution].lengthFitness and \
                            population[levelCheck[check]].widthFitness == population[solution].widthFitness:
                        continue
                    else:
                        toRemove.append(check)
                        dominated.append(levelCheck[check])

                if not levelValid:
                    level += 1
                    continue
                else:
                    newLevel = [populationIndex for index, populationIndex in enumerate(levelCheck) if index not in toRemove]
                    newLevel.append(solution)
                    levels[level] = newLevel
                    if dominated:
                        if level+1 > len(levels) - 1:
                            levels.append(dominated)
                        else:
                            levels[level+1] += dominated
                    levelFound = True

        return levels

    def getFrontDominanceProportions(self, front1, front2):
        proportions = []
        front1Num = 0
        front2Num = 0
        for solution in front1:
            for check in front2:
                if solution.lengthFitness > check.lengthFitness and solution.widthFitness >= check.widthFitness:
                    front1Num += 1
                    break
                if solution.widthFitness > check.widthFitness and solution.lengthFitness >= check.lengthFitness:
                    front1Num += 1
                    break

        for solution in front2:
            for check in front1:
                if solution.lengthFitness > check.lengthFitness and solution.widthFitness >= check.widthFitness:
                    front2Num += 1
                    break
                if solution.widthFitness > check.widthFitness and solution.lengthFitness >= check.lengthFitness:
                    front2Num += 1
                    break
        proportions.append(front1Num / len(front1))
        proportions.append(front2Num / len(front2))
        return proportions

    def frontNoChange(self, generations):
        # Front Change Record
        # 0: generation's front was the same as the previous generation's
        # 1: generation's front was different than the previous generation's
        if len(self.frontChangeRecords) - 1 < generations:
            return False

        check = self.frontChangeRecords[len(self.frontChangeRecords) - generations:]
        if 1 in check:
            return False
        return True
