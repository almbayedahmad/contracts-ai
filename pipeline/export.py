# pipeline/export.py — shim for UI exports
from __future__ import annotations
from typing import Any, Tuple
import io, json, datetime
try:
    import pandas as pd
except Exception:
    pd = None  # يسمح للـ CSV/JSON بالعمل حتى لو ما في pandas

def _to_dataframe(obj: Any):
    if pd is None:
        return None
    try:
        if isinstance(obj, pd.DataFrame):
            return obj
        if isinstance(obj, (list, tuple)):
            if obj and isinstance(obj[0], dict):
                return pd.DataFrame(obj)
            return pd.DataFrame({"values": list(obj)})
        if isinstance(obj, dict):
            # لو dict سطحي: حوّله لصف واحد
            if all(not isinstance(v, (list, dict, tuple)) for v in obj.values()):
                return pd.DataFrame([obj])
            # وإلا جرّبه كـ سجلّات
            return pd.json_normalize(obj)
        # أي شيء آخر: نحاول تحويله لنص
        return pd.DataFrame({"value": [str(obj)]})
    except Exception:
        return None

def export_results(data: Any, fmt: str = "xlsx", base_name: str = "results") -> Tuple[bytes, str, str]:
    """
    يعيد (payload_bytes, mime, filename) لتستخدمها Streamlit:
        st.download_button(..., data=payload, file_name=filename, mime=mime)
    """
    fmt = (fmt or "xlsx").lower()
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    if fmt in ("xlsx", "excel"):
        df = _to_dataframe(data)
        if df is None:
            # لو ما في pandas أو فشل التحويل: نسقط لـ JSON
            payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            return payload, "application/json", f"{base_name}_{stamp}.json"
        bio = io.BytesIO()
        with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="DATA")
        return bio.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f"{base_name}_{stamp}.xlsx"

    if fmt == "csv":
        if pd is not None:
            df = _to_dataframe(data)
            if df is not None:
                payload = df.to_csv(index=False).encode("utf-8")
                return payload, "text/csv", f"{base_name}_{stamp}.csv"
        # بدون pandas: حاول من list[dict] أو dict
        if isinstance(data, (dict, list)):
            payload = json.dumps(data, ensure_ascii=False)
        else:
            payload = str(data)
        return payload.encode("utf-8"), "text/plain", f"{base_name}_{stamp}.csv"

    if fmt == "json":
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        return payload, "application/json", f"{base_name}_{stamp}.json"

    # fallback نصّي
    payload = (str(data) if not isinstance(data, (bytes, bytearray)) else data).encode("utf-8", errors="ignore") if not isinstance(data, (bytes, bytearray)) else data
    return payload, "application/octet-stream", f"{base_name}_{stamp}.bin"
