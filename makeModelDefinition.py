import json
import sys
def main(inputLine, outputName, DBtype, items, listitems, secondaryDBs, dryrun=False, setItemType=None, setDefault=None):
    """
    Function for generating a DataBase model configuration.

    Args:
        outputname (str) : Will be used as default name of the model and as filename\n
        DBtype (str)  : Used to set up the file types for the database. Currently supported: Video, Audio and Text\n
        items (list)  : DB entries with this names will be created as Item\n
        items (list)  : DB entries with this names will be created as ListItem\n
        dryrun (bool) : If True the output json will be printed instead saved\n

    """
    model = {}
    model["General"] = {}
    model["General"]["Name"] = outputName
    model["General"]["Description"] = "Description of {0}".format(outputName)
    if DBtype == "Video":
        model["General"]["Types"] = ["mp4", "wmv", "avi", "mov", "mpg", "mp7",
                                     "flv", "mkv", "f4v", "mpeg"]
    elif DBtype == "Audio":
        model["General"]["Types"] = ["mp3", "wav"]
    else:
        model["General"]["Types"] = ["txt"]
    model["General"]["Separators"] = [".","-","_","+"]
    items = ["ID", "Path", "Added", "Name"]+items
    for item in items:
        model[item] = {}
        model[item]["Type"] = "Item"
        model[item]["default"] = "empty"+item
        model[item]["hide"] = ""
        model[item]["plugin"] = ""
        if item == "ID":
            model[item]["itemType"] = "int"
        elif item == "Added":
            model[item]["itemType"] = "datetime"
        else:
            model[item]["itemType"] = "str"

    listitems = ["Opened", "Changed"]+listitems
    for item in listitems:
        model[item] = {}
        model[item]["Type"] = "ListItem"
        model[item]["default"] = ["empty"+item]
        model[item]["hide"] = ""
        model[item]["plugin"] = ""
        if item == "Opened" or item == "Changed":
            model[item]["itemType"] = "datetime"
        else:
            model[item]["itemType"] = "str"

    if setItemType is not None:
        for item in items+listitems:
            if item in setItemType.keys():
                model[item]["itemType"] = setItemType[item]

    if setDefault is not None:
        for item in items+listitems:
            if item in setItemType.keys():
                model[item]["default"] = setDefault[item]

    for item in secondaryDBs:
        if not (item in items or item in listitems):
            print("Item {0} in secondaryDBs is no valid item of model. Fix arguments and rerun. Exiting....".format(item))
            exit()
    model["General"]["SecondaryDBs"] = secondaryDBs

    model["General"]["CreationCommend"] = " ".join(inputLine)
    if dryrun:
        print(json.dumps(model, sort_keys=True, indent=4, separators=(',', ': ')))
    else:
        with open("conf/{0}.json".format(outputName), 'w') as outfile:
            json.dump(model, outfile, sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    import argparse
    argumentparser = argparse.ArgumentParser(
        description='Function for making a DataBase model'
    )
    argumentparser.add_argument(
        "--output",
        action="store",
        help="Output file name. Saved in conf/",
        type=str,
        required=True
    )

    argumentparser.add_argument(
        "--type",
        action="store",
        help="Sets up default file types for database",
        type=str,
        default="Video",
        choices=["Video", "Audio", "Text"]
    )
    argumentparser.add_argument(
        "--items",
        action="store",
        help="Items that will be put in the config",
        nargs='+',
        type=str,
        default=["SingleItem"]
    )
    argumentparser.add_argument(
        "--listitems",
        action="store",
        help="ListItems that will be put in the config",
        nargs='+',
        type=str,
        default=["ListItem"]
    )
    argumentparser.add_argument(
        "--setItemType",
        action="store",
        help="Sets the itemType of a added item (default is str). \n Pass itemName,type (comma separated w/o space!)",
        nargs='+',
        type=str,
        default=None
    )

    argumentparser.add_argument(
        "--setDefault",
        action="store",
        help="Sets the the default value of a added item (default is empty[Name]). \n Pass itemName,default (comma separated w/o space!)",
        nargs='+',
        type=str,
        default=None
    )

    argumentparser.add_argument(
        "--dryrun",
        action="store_true",
        help="Only print model json instead of saving it",
    )
    argumentparser.add_argument(
        "--secondaryDBs",
        action="store",
        help="Items for which a seconary database will be created",
        nargs="+",
        type=str,
        default=["SingleItem", "ListItem"]
    )

    args = argumentparser.parse_args()
    if args.setItemType is not None:
        setItemType = {}
        for arg in args.setItemType:
            name, newType = arg.split(",")
            setItemType[name] = newType
    else:
        setItemType = None

    if args.setDefault is not None:
        setDefault = {}
        for arg in args.setDefault:
            name, newDefault = arg.split(",")
            setDefault[name] = newDefault
    else:
        setDefault = None

    main(sys.argv, args.output, args.type, args.items, args.listitems, args.secondaryDBs, args.dryrun, setItemType, setDefault)
