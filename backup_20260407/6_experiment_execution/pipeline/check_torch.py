import importlib.util
import sys

spec = importlib.util.find_spec('torch')
if spec is None:
    print('torch_missing')
    sys.exit(1)

import torch
print('torch_ok', torch.__version__)
