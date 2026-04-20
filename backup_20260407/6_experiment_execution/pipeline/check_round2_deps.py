missing = []
for name in ["numpy", "pandas", "sklearn", "torch", "xgboost"]:
    try:
        __import__(name)
    except Exception:
        missing.append(name)

if missing:
    print("missing:", ",".join(missing))
else:
    print("all_ok")
