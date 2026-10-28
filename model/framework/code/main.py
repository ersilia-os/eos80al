# imports
import os
import sys

import pin_kernels  # noqa: F401  keep first: must run before numpy or turbovec load

from ersilia_pack_utils.core import read_smiles, write_out

from predict import TOP, neighbours

# parse arguments
input_file = sys.argv[1]
output_file = sys.argv[2]

# current file directory
root = os.path.dirname(os.path.abspath(__file__))


# my model
def my_model(smiles_list):
    return neighbours(smiles_list)


# read SMILES from .csv file, assuming one column with header
_, smiles_list = read_smiles(input_file)

# run model
outputs = my_model(smiles_list)

# check input and output have the same lenght
input_len = len(smiles_list)
output_len = len(outputs)
assert input_len == output_len

header = [f"smi_{str(i).zfill(2)}" for i in range(TOP)]

# write output in a .csv file
write_out(outputs, header, output_file)
