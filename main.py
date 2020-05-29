from setup import Setup
from evolution import EvolutionEngine
from log import Logger
from solution import SolutionGenerator
from solution import SolutionTracker


def ea(setup):
    logger = Logger(setup.configDict)
    solutionTracker = SolutionTracker()
    logger.createLog()
    bestFoundFront = []
    for run in range(setup.configDict["numRuns"]):
        if setup.configDict["verbose"]:
            print("\n\n---------Run #" + str(run+1) + "------------")
        logger.addRunHeader(run + 1)
        evolutionEngine = EvolutionEngine(setup.configDict, setup.problemSpecs)
        evolutionEngine.evolvePopulation()
        result = evolutionEngine.solutionTracker.bestFront

        if not bestFoundFront:
            bestFoundFront = result
        else:
            proportions = solutionTracker.getFrontDominanceProportions(result, bestFoundFront)
            if proportions[0] > proportions[1]:
                bestFoundFront = result

    logger.logBestSolution(bestFoundFront)


def randomSearch(setup):
    logger = Logger(setup.configDict)
    logger.createLog()
    bestFoundFitness = 0
    bestFoundSolution = []
    for run in range(setup.configDict["numRuns"]):
        bestRunFitness = 0
        bestRunSolution = []
        logger.addRunHeader(run + 1)
        solutionGen = SolutionGenerator(setup.problemSpecs)
        for evals in range(setup.configDict["numEvals"]):
            solution = solutionGen.getRandomSolution()
            fitness = solutionGen.problemSpecs["maxSheetLength"] - solution.length
            if fitness > bestRunFitness:
                logger.addIndividual(evals + 1, fitness)
                bestRunFitness = fitness
                bestRunSolution = solution.shapeCoords

        if bestRunFitness > bestFoundFitness:
            bestFoundFitness = bestRunFitness
            bestFoundSolution = bestRunSolution

    logger.logBestSolution(bestFoundSolution)


def main():
    # Load all configurations and store them for easy access.
    setup = Setup()
    if setup.configDict["algorithmType"] == "ea":
        ea(setup)
    else:
        randomSearch(setup)


if __name__ == "__main__":
    main()
