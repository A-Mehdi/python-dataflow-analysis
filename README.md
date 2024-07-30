# UW CS842 Course Project: Dataflow analysis and optimization transformations on Python programs.

## Usage
You will need python 3.12 to run the project as it relies on the `match` keyword introduced recently in Python.

There are two modes of operation:

* Mode 0: analyze the program
    Analyze variable dependencies in three steps:
    
    * Pick function name

    * Pick variable number

    * Pick line number (dependencies can change for a variable at different points in program)


    Analysis results will include line numbers for the dependent variables and there will be line numbers with fraction which represents dummy line numbers inserted after `if` conditions and `for` loops. You can refer to the `example.txt` file for an example output when analysis is executed on `tests\test5_analysis.py`.
* Mode 1: apply optimizations

    In this mode, program will apply optimizations and print out the transformed code

## How to run
To run the the program, run the `main.py` file and provide 2 arguments:

* Path to the file to examine, transform

* Mode of operation: 0 or 1

* Example: `python main.py tests\test1_transform.py 1`

## Tests
You can refer to the test programs under the `tests` directory. Ones that have `transform` in their name are for testing optimization transformations and ones that have `analysis` in their name are for testing both analysis and transformations.