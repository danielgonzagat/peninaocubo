import os
if os.getenv("PENIN_ENABLE_VIDA_HOOK","0") == "1":
    try:
        from penin.omega.life_hook_patch import auto_patch
        patched = auto_patch()
        print(f"[VIDA+] hook ativo — patched={patched}")
    except Exception as e:
        print(f"[VIDA+] hook falhou: {e}")
