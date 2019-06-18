#! python -v
# -*- coding: utf-8 -*-

from os.path import *

# Switch on/off debug information for program
DEBUG_MODE = False

# If DEBUG_MODE = True, then include directory, where contains refal program
TEST_DIRECTORY = join(dirname(dirname(__file__)), 'tests', 'files').replace("\\", "/")

# List of default Refal-functions
DEFAULT_FUNCTIONS = ["Mu", "Add", "Arg", "Br", "Card", "Chr", "Cp", "Dg", "Dgall", "Div", "Divmod",
                     "Explode", "First", "Get", "Implode", "Last", "Lenw", "Lower", "Mod", "Mul",
                     "Numb", "Open", "Ord", "Print", "Prout", "Put", "Putout", "Rp", "Step",
                     "Sub", "Symb", "Time", "Type", "Upper", "Freeze", "Dn",
                     "Up", "Ev-met", "Residue", "System", "Exit", "Close", "ExistFile", "GetCurrentDirectory",
                     "RemoveFile", "SizeOf", "GetPID", "GetPPID",
                     "Implode_Ext", "Explode_Ext", "TimeElapsed", "Compare", "Random", "RandomDigit", "Write",
                     "ListOfBuiltin", "Sysfun", "DeSysfun", "XMLParse", "GetEnv"]

# Delimiter when needs to divide information
LINE_DELIMITER = "=================="
