import sys
import json
import random
import time


# Gets the problem and configuration file paths, extracts the problem data
# and experiment settings.
class Setup:
    def __init__(self):
        self.configDict = {}
        self.problemSpecs = {}
        try:
            self.configDict["problemPath"] = str(sys.argv[1])
            self.configDict["configPath"] = str(sys.argv[2])
        except IndexError:
            print("Please use the format ’./run.sh <problem1-filepath> <configurationfilepath>’")
            sys.exit()

        print("Running experiment...")
        if len(sys.argv) == 4 and str(sys.argv[3]) == "output":
            self.configDict["verbose"] = True
        else:
            self.configDict["verbose"] = False

        self._readJsonData()
        self._readProblem()
        self._seedRNG()
        self._validateConfigurations()

    # Fill config dictionary with user specified settings
    def _readJsonData(self):
        jsonData = self._getJson()

        self.configDict["algorithmType"] = jsonData["experiment-settings"]["algorithm"]["type"]
        self.configDict["numRuns"] = int(jsonData["experiment-settings"]["number-of-runs"])
        self.configDict["numEvals"] = int(jsonData["experiment-settings"]["fitness-evaluations"])
        self.configDict["rngType"] = jsonData["experiment-settings"]["rng"]["type"]
        self.configDict["rngSeed"] = jsonData["experiment-settings"]["rng"]["seed"]

        self.configDict["initialization"] = jsonData["ea-settings"]["initialization-strategy"]
        if jsonData["ea-settings"]["population-seeding"] == "true":
            self.configDict["populationSeeding"] = True
        else:
            self.configDict["populationSeeding"] = False
        self.configDict["parentSelection"] = jsonData["ea-settings"]["parent-selection"]
        self.configDict["survivalSelection"] = jsonData["ea-settings"]["survival"]["selection"]
        self.configDict["survivalStrategy"] = jsonData["ea-settings"]["survival"]["strategy"]
        self.configDict["termination"] = jsonData["ea-settings"]["termination"]
        self.configDict["populationSize"] = int(jsonData["ea-settings"]["strategy-parameters"][
                                      "mu-population-size"])
        self.configDict["offspringCount"] = int(jsonData["ea-settings"]["strategy-parameters"][
                                      "lambda-offspring-count"])
        self.configDict["parentTournament"] = int(jsonData["ea-settings"]["strategy-parameters"][
                                        "parent-tournament-size"])
        self.configDict["survivalTournament"] = int(jsonData["ea-settings"]["strategy-parameters"][
                                          "parent-tournament-size"])
        self.configDict["mutationRate"] = float(
            jsonData["ea-settings"]["strategy-parameters"]["mutation-rate"])
        self.configDict["frontNoChangeGens"] = int(jsonData["ea-settings"]["strategy-parameters"][
                                       "no-change-in-front-generations"])

        self.configDict["solutionFilePath"] = jsonData["file-settings"]["solution-file-path"]
        self.configDict["logFilePath"] = jsonData["file-settings"]["log-file-path"]
        self.configDict["seedFilePath"] = jsonData["file-settings"]["population-seed-file-path"]

    # Get information from configuration file in JSON format.
    def _getJson(self):
        # Retrieves settings from user-given config file.
        try:
            with open(self.configDict["configPath"], 'r') as file:
                data = file.read()
        except FileNotFoundError:
            print("Configuration file could not be opened.")
            sys.exit()

        jsonData = json.loads(data)
        return jsonData

    def _readProblem(self):
        # Makes an array of the lines of the problem instance file.
        try:
            with open(self.configDict["problemPath"], 'r') as file:
                problemData = []
                for line in file:
                    problemData.append(line.rstrip('\n'))
        except FileNotFoundError:
            print("Problem file could not be opened.")
            sys.exit()

        problemInfo = problemData[0].split()
        del problemData[0]
        for stepSet in range(len(problemData)):
            problemData[stepSet] = problemData[stepSet].split()

        self.problemSpecs["shapeInfo"] = problemData
        self.problemSpecs["sheetWidth"] = int(problemInfo[0])
        self.problemSpecs["numOfShapes"] = int(problemInfo[1])

    def _seedRNG(self):
        # Seeds the RNG based on user's settings.
        if self.configDict["rngType"] == "seed":
            random.seed(self.configDict["rngSeed"])
        elif self.configDict["rngType"] == "time":
            rngSeed = int(round(time.time() * 1000))
            self.configDict["rngSeed"] = rngSeed
            random.seed(rngSeed)
        else:
            print("Invalid RNG type.")
            sys.exit()

    def _validateConfigurations(self):
        if self.configDict["algorithmType"] != "random" and self.configDict["algorithmType"] !=  "ea":
            print("Invalid algorithm type, please refer to README.")
            sys.exit()

        if self.configDict["numRuns"] <= 0:
            print("Invalid number of runs.")
            sys.exit()

        if self.configDict["numEvals"] <= 0:
            print("Invalid number of evaluations.")
            sys.exit()
