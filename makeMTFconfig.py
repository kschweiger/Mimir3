import json
import sys

def main(model, system, dryrun, queryItems):
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
    modelDatetimeItems = []

    for section in modelDict:
        if "Type" in modelDict[section].keys():
            if modelDict[section]["Type"] == "ListItem":
                modelListItems.append(section)
            elif modelDict[section]["Type"] == "Item":
                modelSingleItems.append(section)
            else:
                raise RuntimeError("Section %s has no valid type. Found %s"%(section, modelDict[section]["Type"]))
        if "itemType" in modelDict[section].keys():
            if modelDict[section]["itemType"] == "datetime":
                modelDatetimeItems.append(section)

    modelItems = modelSingleItems+modelListItems

    config = {}
    config["General"] = {}
    config["General"]["Width"] = 110
    config["General"]["Height"] = 50

    if system == "Linux":
        config["General"]["Executable"] = "mimir/frontend/terminal/executable/linux/runVLC.sh"
    elif system == "macOS":
        config["General"]["Executable"] = "mimir/frontend/terminal/executable/macOS/runVLC.sh"
    else:
        raise NotImplementedError

    config["General"]["QueryItems"] = queryItems
    config["General"]["DisplayItems"] = []
    config["General"]["AllItems"] = []
    config["General"]["ModItems"] = []
    for item in modelItems:
        config["General"]["DisplayItems"].append(item)
        config["General"]["AllItems"].append(item)
        config[item] = {}
        config[item]["DisplayName"] = item
        config[item]["DisplayDefault"] = None
        if item in modelListItems:
            config[item]["nDisplay"] = 99
            config[item]["Priority"] = []
            config[item]["Hide"] = []
            config[item]["Type"] = "ListItem"
            config[item]["ShowOnly"] = "All"
        else:
            config[item]["maxLen"] = 99
            config[item]["Type"] = "Item"
        if item in modelDatetimeItems:
            config[item]["modDisplay"] = "Full" #Full, Date, Time
    config["Name"]["maxLen"] = 32

    config["General"]["DisplayItems"].append("timesOpened")
    config["General"]["AllItems"].append("timesOpened")
    config["timesOpened"] = {}
    config["timesOpened"]["DisplayName"] = "nOpened"
    config["timesOpened"]["DisplayDefault"] = None
    config["timesOpened"]["Type"] = "Counter"
    config["timesOpened"]["Base"] = "Opened"

    outputName = model.split("/")[-1].replace(".json", "")
    config["General"]["Windows"] = ["Main", "List", "DB","Modify","MultiModify"]

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
                                           ("Modify","Enter modification mode"),
                                           ("Execute","Execute a database entry"),
                                           ("Random","Execute a random entry from the last printed list"),
                                           ("Query","Print entries returned by a query. Will query items: {0}".format(", ".join(config["General"]["QueryItems"]))),
                                           ("Newest","Print latest entries")]
    config["Window"]["DB"] = {}
    config["Window"]["DB"]["Type"] = "Window"
    config["Window"]["DB"]["Title"] = "Database optins"
    config["Window"]["DB"]["Text"] = ["This collections options on the database"]
    config["Window"]["DB"]["Options"] = [("Main", "Back to main menu"),
                                         ("Save","Saves the current state of the database"),
                                         ("Read FS","Invokes a search for new files from the mimir root dir")]

    config["Window"]["Modify"] = {}
    config["Window"]["Modify"]["Type"] = "Window"
    config["Window"]["Modify"]["Title"] = "Database modification"
    config["Window"]["Modify"]["Text"] = ["Modifications"]
    config["Window"]["Modify"]["Options"] = [("Main", "Back to main menu"),
                                             ("Single Entry","Will spawn a window where one entry can be modified mulitple times"),
                                             ("Entry Range","Modify a range of entries multiple times. Input ** XXX - YYY ***"),
                                             ("List Range","Modify a list of entries multiple times. Input comma separted list")]

    config["Window"]["MultiModify"] = {}
    config["Window"]["MultiModify"]["Type"] = "Window"
    config["Window"]["MultiModify"]["Title"] = "Multiple modifications of one entry"
    config["Window"]["MultiModify"]["Text"] = ["Multi modification for: "]
    config["Window"]["MultiModify"]["Options"] = [("Main", "Back to main menu")]
    for item in modelItems:
        if item in ["ID", "Path", "Opened", "Changed", "Added"]:
            continue
        config["Window"]["MultiModify"]["Options"].append((item, "Some description"))
        config["General"]["ModItems"].append(item)

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
        "--system",
        action="store",
        help="System that will run MTF. Required for executable",
        type=str,
        required=True,
        choices=["Linux", "macOS"]
    )
    argumentparser.add_argument(
        "--dryrun",
        action="store_true",
        help="Only print model json instead of saving it",
    )
    argumentparser.add_argument(
        "--queryItems",
        action="store",
        help="Pass items that are considered for database queries",
        nargs = "+",
        default = ["SingleItem", "ListItem"]
    )


    args = argumentparser.parse_args()

    main(args.inputModel, args.system, args.dryrun, args.queryItems)
