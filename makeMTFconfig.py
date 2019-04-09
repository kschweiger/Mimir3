import json
import sys

def main(model, dryrun):
    """
    Function for creating a MTF config based on a passed model.json

    Args:
        model (str) : Input model.json created with makeModelDefinition.py. Will be used to set MTF configuration based on defined Items
    """
    modelDict = None
    with open(model) as f:
        modelDict = json.load(f)

    modelSingleItems = []
    modelListItems = []

    for section in modelDict:
        if "Type" in modelDict[section].keys():
            if modelDict[section]["Type"] == "ListItem":
                modelListItems.append(section)
            elif modelDict[section]["Type"] == "Item":
                modelSingleItems.append(section)
            else:
                raise RuntimeError("Section %s has no valid type. Found %s"%(section, modelDict[section]["Type"]))

    modelItems = modelSingleItems+modelListItems

    config = {}
    config["General"] = {}
    config["General"]["Width"] = 80
    config["General"]["Height"] = 50
    config["General"]["DisplayItems"] = []
    for item in modelItems:
        config["General"]["DisplayItems"].append(item)
        config[item] = {}
        config[item]["DisplayName"] = item
        if item in modelListItems:
            config[item]["nDisplay"] = 99
            config[item]["Priority"] = []
            config[item]["Hide"] = []
            config[item]["Type"] = "ListItem"
        else:
            config[item]["maxLen"] = 99
            config[item]["Type"] = "Item"
    config["Name"]["maxLen"] = 32
    outputName = model.split("/")[-1].replace(".json", "")
    config["General"]["Windows"] = ["Main", "List", "DB"]

    config["Window"] = {}
    config["Window"]["Main"] = {}
    config["Window"]["Main"]["Type"] = "Window"
    config["Window"]["Main"]["Title"] = "Main Window of MTF"
    config["Window"]["Main"]["Text"] = ["This is a config generated from "+str(model),
                                        "The Following options are available for interaction"]
    config["Window"]["Main"]["Options"] = [("Exit", "Exit MTF"),
                                           ("Execute","Execute a database entry"),
                                           ("Modify","Enter modification mode"),
                                           ("List","Enter list mode"),
                                           ("Random","Execute a random entry"),
                                           ("DB Option","Database options (save, etc.)")]
    config["Window"]["List"] = {}
    config["Window"]["List"]["Type"] = "ListWindow"
    config["Window"]["List"]["Title"] = "MTF Lists"
    config["Window"]["List"]["Text"] = None
    config["Window"]["List"]["Options"] = [("Main", "Back to main menu"),
                                           ("All","Prints all entries"),
                                           ("Query","Print entries returned by a query"),
                                           ("Newest","Print latest entries")]
    config["Window"]["DB"] = {}
    config["Window"]["DB"]["Type"] = "Window"
    config["Window"]["DB"]["Title"] = "Database optins"
    config["Window"]["DB"]["Text"] = ["This collections options on the database"]
    config["Window"]["DB"]["Options"] = [("Main", "Back to main menu"),
                                         ("Save","Saves the current state of the database"),
                                         ("Read FS","Invokes a search for new files from the mimir root dir")]


    if dryrun:
        print(json.dumps(config, sort_keys=True, indent=4, separators=(',', ': ')))
    else:
        with open("conf/MTF_{0}.json".format(outputName), 'w') as outfile:
            json.dump(config, outfile, sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    import argparse
    argumentparser = argparse.ArgumentParser(
        description='Function generating the MTF definitons from a given model'
    )
    argumentparser.add_argument(
        "--inputModel",
        action="store",
        help="Input model",
        type=str,
        required=True
    )
    argumentparser.add_argument(
        "--dryrun",
        action="store_true",
        help="Only print model json instead of saving it",
    )
    args = argumentparser.parse_args()

    main(args.inputModel, args.dryrun)
