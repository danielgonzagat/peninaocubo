import os
from scripts._common_fusion import load_plan

def test_policy_staging():
    os.environ["FUSE_POLICY"] = "staging"
    p = load_plan("fusion/megaIAAA.plan")
    assert p["_policy_file"].endswith(".staging.yaml")

def test_policy_strict():
    os.environ["FUSE_POLICY"] = "strict"
    p = load_plan("fusion/megaIAAA.plan")
    assert p["_policy_file"].endswith(".strict.yaml")

def test_policy_default():
    os.environ.pop("FUSE_POLICY", None)
    p = load_plan("fusion/megaIAAA.plan")
    assert p["_policy_file"].endswith(".plan.yaml")
