import sys
from analysis import runInteractive
from transform import transformLoop

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Arguments invalid")
        exit()
    filePath = sys.argv[1]
    modeOfOperation = sys.argv[2]
    if modeOfOperation == '0':
        runInteractive(filePath)
    elif modeOfOperation == '1':
        transformLoop(filePath)
