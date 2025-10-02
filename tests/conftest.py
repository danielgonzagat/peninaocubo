import sys, multiprocessing as mp
if sys.platform == "darwin":
    try:
        mp.set_start_method("fork", force=True)
    except RuntimeError:
        # já setado; segue o baile
        pass
