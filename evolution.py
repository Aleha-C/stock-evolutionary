import random
import sys
from solution import SolutionGenerator
from solution import Solution
from solution import SolutionTracker
from log import Logger


class EvolutionEngine:
    def __init__(self, configDict, problemSpecs):
        self.configDict = configDict
        self.problemSpecs = problemSpecs
        self.evalsLeft = self.configDict["numEvals"]
        self.solutionGen = SolutionGenerator(self.problemSpecs)
        self.solutionTracker = SolutionTracker()
        self.logger = Logger(self.configDict)
        self.problemSpecs["maxSheetLength"] = self.solutionGen.problemSpecs["maxSheetLength"]
        self.population = self._initializePopulation()

    def evolvePopulation(self):
        endOfRun = False
        if self.evalsLeft == 0:
            endOfRun = True
        evalsCompleted = self.configDict["populationSize"]
        while not endOfRun:
            offspringPool = []
            for evaluation in range(self.configDict["offspringCount"]):
                if self.evalsLeft == 0:
                    endOfRun = True
                    break

                offspring = self._createOffspring()
                offspringPool.append(offspring)
                evalsCompleted += 1
                self.evalsLeft -= 1

            survivors = self._survivalSelection(offspringPool)
            self.population = survivors
            self.solutionTracker.addGeneration(self.population)
            self.logger.addGeneration(evalsCompleted, self.solutionTracker.bestLengthFitnessRecords[-1],
                                      self.solutionTracker.averageLengthFitnessRecords[-1],
                                      self.solutionTracker.bestWidthFitnessRecords[-1],
                                      self.solutionTracker.averageWidthFitnessRecords[-1])

            if self._willTerminate():
                endOfRun = True

        return self.solutionTracker.bestFront

    def _initializePopulation(self):
        population = []
        remainingPopulation = self.configDict["populationSize"]
        if self.configDict["populationSeeding"]:
            population = self._getSeededIndividuals()
            remainingPopulation -= len(population)

        randomGenPopulation = self._getRandomIndividuals(remainingPopulation)
        population += randomGenPopulation
        population = self._shufflePopulation(population.copy())

        self.solutionTracker.addGeneration(population)
        # For front convergence tracking, the front changed from empty to full.
        self.solutionTracker.frontChangeRecords.append(1)
        self.logger.addGeneration(self.configDict["populationSize"], self.solutionTracker.bestLengthFitnessRecords[-1],
                                  self.solutionTracker.averageLengthFitnessRecords[-1],
                                  self.solutionTracker.bestWidthFitnessRecords[-1],
                                  self.solutionTracker.averageWidthFitnessRecords[-1])
        return population

    def _getSeededIndividuals(self):
        try:
            with open(self.configDict["seedFilePath"], 'r') as file:
                seedData = []
                for line in file:
                    seedData.append(line.rstrip('\n'))
        except FileNotFoundError:
            print("Population seed file could not be opened.")
            sys.exit()

        solutionLength = self.problemSpecs["numOfShapes"]
        numberOfSolutions = int(seedData[0])
        del seedData[0]

        # Only retrieve first mu solutions from seed file if it contains more than mu solutions
        if numberOfSolutions > self.configDict["populationSize"]:
            numberOfSolutions = self.configDict["populationSize"]

        population = []
        for solution in range(numberOfSolutions):
            if self.evalsLeft == 0:
                break

            solutionCoords = []
            for coord in range(solutionLength):
                addCoord = seedData[0]
                del seedData[0]
                addCoord = [int(num) for num in addCoord.split(",")]
                solutionCoords.append(addCoord)
            if seedData:
                del seedData[0]

            if not self.solutionGen.solutionIsValid(solutionCoords):
                continue

            solutionDimensions = self.solutionGen.getSheetDimensionsConstrained(solutionCoords)
            length = solutionDimensions[1] + 1
            width = solutionDimensions[3] + 1
            newSolution = Solution(solutionCoords, length, width)
            newSolution.lengthFitness = self.problemSpecs["maxSheetLength"] - length
            newSolution.widthFitness = self.problemSpecs["sheetWidth"] - width
            population.append(newSolution)
            self.evalsLeft -= 1

        return population

    def _getRandomIndividuals(self, size):
        if size == 0:
            return []

        population = []
        for individual in range(size):
            if self.evalsLeft == 0:
                break
            indiv = self.solutionGen.getRandomSolution()
            population.append(indiv)
            self.evalsLeft -= 1

        return population

    def _shufflePopulation(self, population):
        random.shuffle(population)
        return population

    def _createOffspring(self):
        parent1Index, parent2Index = self._selectParents()
        parent1, parent2 = self.population[parent1Index], self.population[parent2Index]
        offspring = self._recombine(parent1, parent2)
        if self.configDict["mutationRate"] > 0:
            offspring = self._mutateOffspring(offspring.copy())

        offspringDimensions = self.solutionGen.getSheetDimensionsConstrained(offspring)
        offspringLength = offspringDimensions[1] + 1
        offspringWidth = offspringDimensions[3] + 1
        mutatedOffspringSolution = Solution(offspring, offspringLength, offspringWidth)
        mutatedOffspringSolution.lengthFitness = self.problemSpecs["maxSheetLength"] - offspringLength
        mutatedOffspringSolution.widthFitness = self.problemSpecs["sheetWidth"] - offspringWidth
        return mutatedOffspringSolution

    def _selectParents(self):
        if self.configDict["parentSelection"] == "k-tournament":
            parent1Index = self._kTournament(self.population, self.configDict["parentTournament"])
            parent2Index = self._kTournament(self.population, self.configDict["parentTournament"])
        elif self.configDict["parentSelection"] == "fitness-proportional":
            parent1Index, parent2Index = self._parentFitnessProportional()
        else:
            parent1Index, parent2Index = self._uniformRandomParents()

        return parent1Index, parent2Index

    def _kTournament(self, population, tournamentSize):
        if len(population) < tournamentSize:
            tournamentSize = len(population)

        levels = self.solutionTracker.getLevels(population)
        levelToIndex = [0] * len(population)
        for level in range(len(levels)):
            for ind in levels[level]:
                levelToIndex[ind] = level

        participantIndex = []
        winnerIndex = -1
        for choice in range(tournamentSize):
            while True:
                index = random.randint(0, len(population) - 1)
                if index not in participantIndex:
                    participantIndex.append(index)
                    if winnerIndex == -1:
                        winnerIndex = index
                        break
                    if levelToIndex[index] > levelToIndex[winnerIndex]:
                        winnerIndex = index
                    break

        return winnerIndex

    def _parentFitnessProportional(self):
        fitnessProportions = self._calcFitnessProportions(self.population)
        parentIndices = []

        totalProb = 0
        for probability in fitnessProportions:
            totalProb += probability

        validParents = False
        while not validParents:
            place = 0
            index = 0
            randFloat = random.uniform(0, totalProb)
            for probability in fitnessProportions:
                if randFloat <= (place + probability):
                    if index not in parentIndices:
                        parentIndices.append(index)
                        if len(parentIndices) == 2:
                            validParents = True
                        break
                    else:
                        break
                else:
                    place += probability
                    index += 1
        return parentIndices[0], parentIndices[1]

    def _calcFitnessProportions(self, population):
        levels = self.solutionTracker.getLevels(population)
        fitnessProportions = [0] * len(population)
        currVal = 100
        levelValues = []
        for level in levels:
            levelValues.append(currVal)
            currVal /= 2

        for level in range(len(levels)):
            for solution in levels[level]:
                fitnessProportions[solution] = levelValues[level]

        currProb = fitnessProportions[0]
        for prob in range(1, len(fitnessProportions)):
            currProb += fitnessProportions[prob]
            fitnessProportions[prob] = currProb

        return fitnessProportions

    def _uniformRandomParents(self):
        parentIndices = [random.randint(0, len(self.population) - 1)]
        parent2 = random.randint(0, len(self.population) - 1)
        while parent2 in parentIndices:
            parent2 = random.randint(0, len(self.population) - 1)
        parentIndices.append(parent2)

        return parentIndices[0], parentIndices[1]

    def _recombine(self, parent1, parent2):
        offspring = self._crossover(parent1, parent2)
        return offspring

    def _crossover(self, parent1, parent2):
        offspringCoords = []
        for geneNum in range(len(parent1.shapeCoords)):
            whichParent = random.randint(0, 1)
            addGene = []
            if whichParent == 0:
                addGene = parent1.shapeCoords[geneNum]
            else:
                addGene = parent2.shapeCoords[geneNum]
            offspringCoords = self.solutionGen.addNewGene(geneNum, addGene, offspringCoords.copy())

        return offspringCoords

    def _mutateOffspring(self, offspring):
        probabilities = []
        mutationRate = self.configDict["mutationRate"]
        for gene in range(len(offspring)):
            probabilities.append(random.uniform(0, 1))
        for gene in range(len(offspring)):
            if probabilities[gene] < mutationRate:
                offspring[gene] = []
        mutated = self.solutionGen.addMutations(offspring)

        return mutated

    def _survivalSelection(self, offspringPool):
        selectionPopulation = []
        poolSize = self.configDict["populationSize"]
        if self.configDict["survivalStrategy"] == "comma":
            if len(offspringPool) < self.configDict["populationSize"]:
                poolSize = len(offspringPool)
            selectionPopulation = offspringPool.copy()
        else:
            selectionPopulation = offspringPool.copy() + self.population.copy()

        selectionPopulation = self._shufflePopulation(selectionPopulation.copy())
        survivors = []
        if self.configDict["survivalSelection"] == "uniform-random":
            survivors = self._randomSurvival(selectionPopulation, poolSize)
        elif self.configDict["survivalSelection"] == "truncation":
            survivors = self._truncationSurvival(selectionPopulation, poolSize)
        elif self.configDict["survivalSelection"] == "fitness-proportional":
            survivors = self._proportionalSurvival(selectionPopulation, poolSize)
        elif self.configDict["survivalSelection"] == "k-tournament":
            survivors = self._tournamentSurvival(selectionPopulation, poolSize)

        return survivors

    def _randomSurvival(self, selectionPopulation, poolSize):
        survivors = []
        survivorIndices = []
        for survivor in range(poolSize):
            choice = random.randint(0, len(selectionPopulation) - 1)
            while choice in survivorIndices:
                choice = random.randint(0, len(selectionPopulation) - 1)
            survivorIndices.append(choice)

        for survivor in survivorIndices:
            survivors.append(selectionPopulation[survivor])

        return survivors

    def _truncationSurvival(self, selectionPopulation, poolSize):
        survivors = []
        levels = self.solutionTracker.getLevels(selectionPopulation)
        levelArr = []
        for level in levels:
            levelArr += level

        survivorInds = levelArr[:poolSize]
        for survivor in survivorInds:
            survivors.append(selectionPopulation[survivor])

        return survivors

    def _proportionalSurvival(self, selectionPopulation, poolSize):
        survivors = []
        survivorIndices = []
        proportions = self._calcFitnessProportions(selectionPopulation)
        totalProb = 0
        for probability in proportions:
            totalProb += probability

        poolFull = False
        while not poolFull:
            place = 0
            index = 0
            randFloat = random.uniform(0, totalProb)
            for prob in proportions:
                if randFloat <= (place + prob):
                    if index not in survivorIndices:
                        survivorIndices.append(index)
                        if len(survivorIndices) == poolSize:
                            poolFull = True
                            break
                    else:
                        break
                else:
                    place += prob
                    index += 1
        for survivor in survivorIndices:
            survivors.append(selectionPopulation[survivor])
        return survivors

    def _tournamentSurvival(self, selectionPopulation, poolSize):
        survivorIndices = []
        survivors = []
        remaining = selectionPopulation.copy()
        for survivor in range(poolSize):
            winner = self._kTournament(remaining.copy(), self.configDict["survivalTournament"])
            survivors.append(remaining.copy()[winner])
            del remaining[winner]

        return survivors

    def _willTerminate(self):
        if self.evalsLeft == 0:
            return True
        elif self.configDict["termination"] == "no-change-in-front" and \
                self.solutionTracker.frontNoChange(self.configDict["frontNoChangeGens"]):
            return True
        else:
            return False
