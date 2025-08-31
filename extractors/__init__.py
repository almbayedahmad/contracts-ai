# extractors/__init__.py — shim package
# نحاول أولًا استخدام extractors الحقيقية من الباكند (backend/app/extractors)
try:
    from app.extractors import *  # type: ignore
except Exception:
    # بديل dummy لو ما كان فيه app.extractors
    from .dummy import *  # type: ignore

# كدالة أمان: أي استدعاء غير معروف يرجع extract_all
def __getattr__(name: str):
    if name in ("extract", "run", "run_all"):
        from .dummy import extract_all
        return extract_all
    raise AttributeError(name)
