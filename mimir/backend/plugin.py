"""
Module for processing plugins set for certain Items in the model definition
"""
import logging
import os
import re

import hachoir.metadata
import hachoir.parser

logger = logging.getLogger(__name__)


def get_VideoMetaData(fileName):
    """
    Get video metadata for height, weight and duration using hachior.

    Args:
        fileName (str) : Path to a file (Should not crash for none video files ;))

    Returns:
        dict : Dict keys are width, height, duration
    """
    thisMetaData = hachoir.metadata.extractMetadata(
        hachoir.parser.createParser(fileName)
    )
    if thisMetaData is None:
        voi_width, voi_height, voi_duration = -1, -1, "00:00:00"
    else:
        try:
            voi_width = thisMetaData.get("width")
        except ValueError:
            voi_width = -1
        try:
            voi_height = thisMetaData.get("height")
        except ValueError:
            voi_height = -1
        try:
            voi_duration = str(thisMetaData.get("duration"))
            logger.debug("voi_duration from hachoir: %s", voi_duration)
            voi_duration = voi_duration.split(".")[0]
        except ValueError:
            voi_duration = "00:00:00"
        voi_duration_h, voi_duration_min, voi_duration_sec = voi_duration.split(":")
        voi_duration = "{0:02d}:{1:02d}:{2:02d}".format(
            int(voi_duration_h), int(voi_duration_min), int(voi_duration_sec)
        )
        logger.debug("voi_duration formatted: %s", voi_duration)

    return {
        "width": str(voi_width),
        "height": str(voi_height),
        "duration": voi_duration,
    }


def get_osData(filename, SF=1e9):
    """
    Get information of the file from the os

    Args:
        filename (str) : Path to a file
        SF (int) : Rescale size (stat returns bytes). Default converts to GB

    Returns:
        dict : Dict keys are: size
    """
    filesize = os.path.getsize(filename)
    filesize = filesize / SF
    return {"size": "{0:.2f}".format(filesize)}


def getPluginValues(fileName, pluginDefs, modules=["VideoMetaData", "osData"]):
    """
    Wrapper that can decode the definitions in the database model for the plugin

    Args:
        fileName (str) : Path to a file
        pluginDefs (list) : List of plugins (in form module:value)
                            -> Get from model.pluginDefinitions
        modules (list) : Not intended to be passed by user. Just defines the plugins
                         usable

    Returns:
        dict : Dict keys are module:value and values are the plugin return values
    """
    runVideoMetaData = False
    runosData = False
    for definition in pluginDefs:
        check = re.search("[a-zA-Z0-9]+:[a-zA-Z0-9]+", definition)
        if check is None:
            raise ValueError(
                "%s is no valid plugin. Should be 'module:value'" % definition
            )
        else:
            if check.span() != (0, len(definition)):
                raise ValueError(
                    "%s is no valid pluging. Check Definition" % definition
                )
        module, value = definition.split(":")
        if module not in modules:
            raise ValueError("Module %s not defined")
        if "VideoMetaData" in definition:
            runVideoMetaData = True
        if "osData" in definition:
            runosData = True
    if runVideoMetaData:
        VideoMetaData = get_VideoMetaData(fileName)
    if runosData:
        osData = get_osData(fileName)
    values = {}
    for definition in pluginDefs:
        module, value = definition.split(":")
        if module == "VideoMetaData":
            values[definition] = VideoMetaData[value]
        elif module == "osData":
            values[definition] = osData[value]
        else:
            raise NotImplementedError
    return values
