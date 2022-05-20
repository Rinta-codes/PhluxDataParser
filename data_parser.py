#### Version 1.1 ####

import pandas
import os

#### CONSTANTS ####

# filename prefixes
rev_bias_prefix = "Reverse bias"

# folder prefixes
unit_cell_prefix = "D"
die_prefix = "S"

## constants configurable via config files

try:
    config = pandas.read_csv("config.csv", encoding = "utf-8")
    dice = pandas.read_csv("dice.csv", encoding = "utf-8")
except:
    print("One of the configuration files is missing or empty")

data_path = config.at[0, "Path"]
if not pandas.notnull(data_path):
    data_path = ""
die_size_in_um = config.at[0, "Size"]
voltage = config.at[0, "Voltage"]
current_min = config.at[0, "CurrentMin"]
current_max = config.at[0, "CurrentMax"]

# find row for required Size, retrieve Dice for it, and split them into an array
dice_list = str(dice.loc[dice["Size"] == die_size_in_um, ["Dice"]].iat[0, 0]).split(", ")

# table for storing parsing results - start with empty
results = None
# column names to be used
column_uc = "Unit Cell"
column_die = "Die"
column_size = "Size (μm)"
column_voltage = "Voltage (V)"
column_abs_current = "Abs Current (A)"
column_report = "Report"

#### FILE PARSER ####
# how many times parser was run
parse_count = 0

## for given Die folder path, parces test data and returns it as a single row
def parse(path, unit_cell, die):
    # increment count
    global parse_count
    parse_count += 1

    files = os.listdir(path)
    # find exact Reverse Bias filename based off known prefix
    rev_bias_filename = [file for file in files if file.startswith(rev_bias_prefix)]
    # if any were found - load data from first
    if len(rev_bias_filename) > 0:
        rev_data = pandas.read_csv(f"{path}\{rev_bias_filename[0]}", sep = "\t")

        # locate all rows with specified Voltage
        current_for_voltage_list = rev_data[rev_data.iloc[:, 0] == voltage]
        # if any rows were located - pick Voltage value from the first (we normally expect a single row or none)
        current_for_voltage = current_for_voltage_list.iat[0, 1] if current_for_voltage_list.shape[0] != 0 else 0

        new_row = pandas.DataFrame(
        {
            column_uc : [unit_cell_prefix + str(unit_cell)],
            column_die : [die_prefix + str(die)],
            column_size : [die_size_in_um],
            column_voltage : [voltage],
            column_abs_current : [abs(current_for_voltage) if current_for_voltage != 0 else None],
            # To avoid relying on absolute values & still account for "swapped" min and max
            column_report : [current_min < current_for_voltage < current_max or current_min > current_for_voltage > current_max]
        })

        return new_row

    return None


#### MAIN LOOP ####

## loop through data folders
# starting values for Unit Cell and Die indices
unit_cell_index = 0
die_index_start_value = 1
die_index = die_index_start_value
# loop through Unit Cell folders
while os.path.exists(f"{data_path}{unit_cell_prefix}{str(unit_cell_index)}"):
    # loop through Die folders within Unit Cell folders
    while os.path.exists(f"{data_path}{unit_cell_prefix}{str(unit_cell_index)}\{die_prefix}{str(die_index)}"):
        # run parser only for Dice in the dice list for required size
        if str(die_index) in dice_list:
            parse_result = parse(f"{data_path}{unit_cell_prefix}{str(unit_cell_index)}\{die_prefix}{str(die_index)}", unit_cell_index, die_index)
            results = pandas.concat([results, parse_result])
        # iterate die
        die_index += 1
    # on reaching max available die for selected unit cell - reset die, iterate unit cell
    die_index = die_index_start_value
    unit_cell_index += 1

if parse_count == 0:
    print("No data files were found - check the data path in configuration file, and make sure you specified the list of dice for your required size")

# Export to csv without Index column
if not results.empty:
    results.loc[results["Report"] == True].to_csv('True.csv', index = False)
    results.loc[results["Report"] == False].to_csv('False.csv', index = False)
else:
    # if no data was found - delete old files to not get them confused for new results
    os.remove('True.csv') if os.path.exists('True.csv') else None
    os.remove('False.csv') if os.path.exists('False.csv') else None


#### CHANGELOG ####
# v1.1 
#  - Changed Current comparison to accept reversed min-max without resorting to absolute value comparison
#  - Replace remaining mentions of subsets with dice
# v1.0
#  - First version



