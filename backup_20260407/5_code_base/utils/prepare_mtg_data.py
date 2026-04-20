import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Prepare numeric CSV for MTGNN single-step loader")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output numeric CSV path")
    parser.add_argument("--encoding", default="auto", help="Input file encoding: auto/utf-8/gbk/utf-8-sig")
    parser.add_argument("--max_rows", type=int, default=6000, help="Use only latest N rows; <=0 means all rows")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    encodings = [args.encoding] if args.encoding != "auto" else ["utf-8", "utf-8-sig", "gbk"]
    df = None
    last_err = None
    for enc in encodings:
        try:
            df = pd.read_csv(input_path, encoding=enc)
            break
        except Exception as exc:
            last_err = exc
    if df is None:
        raise RuntimeError(f"Failed to read csv with encodings {encodings}: {last_err}")

    # Drop the first timestamp-like column and keep only numeric features.
    feature_df = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")

    if args.max_rows > 0 and len(feature_df) > args.max_rows:
        feature_df = feature_df.tail(args.max_rows).reset_index(drop=True)

    # Fill missing values to avoid NaN failures in numpy loadtxt.
    feature_df = feature_df.replace([np.inf, -np.inf], np.nan)
    feature_df = feature_df.interpolate(limit_direction="both").ffill().bfill()

    # Drop zero-variance columns to prevent divide-by-zero in MTGNN normalization.
    max_abs = feature_df.abs().max(axis=0)
    feature_df = feature_df.loc[:, max_abs > 1e-8]

    if feature_df.isna().any().any():
        raise ValueError("NaN still exists after filling; please inspect source data")
    if feature_df.shape[1] == 0:
        raise ValueError("No valid feature columns after filtering")

    np.savetxt(output_path, feature_df.to_numpy(dtype=np.float32), delimiter=",", fmt="%.6f")

    print(f"saved_numeric_csv={output_path}")
    print(f"num_rows={feature_df.shape[0]}")
    print(f"num_nodes={feature_df.shape[1]}")


if __name__ == "__main__":
    main()
