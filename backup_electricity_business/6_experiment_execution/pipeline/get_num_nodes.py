import argparse
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()

    arr = np.loadtxt(args.data, delimiter=',', max_rows=1)
    if arr.ndim == 0:
        print(1)
    elif arr.ndim == 1:
        print(arr.shape[0])
    else:
        print(arr.shape[1])


if __name__ == '__main__':
    main()
