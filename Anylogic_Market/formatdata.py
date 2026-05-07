import pandas as pd
import os

file_path = 'runs_waitdelivery.txt'

with open(file_path, 'r') as f:
    lines = f.readlines()

print(lines)


