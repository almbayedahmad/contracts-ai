from pathlib import Path
import re

p = Path(r".\app\ui_streamlit.py")
lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()

def indent(s: str) -> int:
    return len(s) - len(s.lstrip(" "))

i = 0
patched_any = False
while i < len(lines):
    line = lines[i]
    # نبحث عن try: على سطر مستقل
    if re.match(r"^\s*try:\s*$", line):
        base_indent = indent(line)

        # 1) تأكيد وجود جسم بعد try (سطر بمسافة أكبر)
        j = i + 1
        # تخطّي الأسطر الفارغة/التعليقات
        while j < len(lines) and (lines[j].strip() == "" or lines[j].lstrip().startswith("#")):
            j += 1
        need_body_pass = True
        if j < len(lines) and indent(lines[j]) > base_indent:
            need_body_pass = False
        if need_body_pass:
            lines.insert(i + 1, " " * (base_indent + 4) + "pass")
            patched_any = True
            j = i + 2  # لأننا أضفنا سطر

        # 2) افحص إذا عندنا except/finally بنفس الإزاحة لاحقًا
        k = j
        have_handler = False
        # امشِ حتى أول سطر يرجع لنفس الإزاحة أو أقل (نهاية جسم try)
        while k < len(lines):
            if lines[k].strip() == "" or lines[k].lstrip().startswith("#"):
                k += 1
                continue
            ind = indent(lines[k])
            if ind == base_indent and re.match(r"^(except\b|finally:)", lines[k].lstrip()):
                have_handler = True
                break
            if ind <= base_indent:
                # انتهى جسم try، ومالقينا except
                break
            k += 1

        if not have_handler:
            insert_pos = k  # قبل أول سطر بنفس/أقل إزاحة، أو نهاية الملف
            handler = [
                " " * base_indent + "except Exception as e:",
                " " * (base_indent + 4) + "pass",
            ]
            lines[insert_pos:insert_pos] = handler
            patched_any = True
            # تقدّم المؤشر بعد الهاندلر عشان ما ندور على نفس try مرة ثانية
            i = insert_pos + len(handler) - 1

    i += 1

if patched_any:
    Path(p).write_text("\n".join(lines) + ("\n" if lines and lines[-1] != "" else ""), encoding="utf-8")
    print("Patched one or more dangling try-blocks.")
else:
    print("No dangling try-blocks found (nothing changed).")
