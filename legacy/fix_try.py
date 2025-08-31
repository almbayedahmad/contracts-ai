from pathlib import Path
import re

p = Path(r".\app\ui_streamlit.py")
src = p.read_text(encoding="utf-8", errors="ignore").splitlines()

def is_blank(line: str) -> bool:
    return line.strip() == ""

def indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" "))]

# 1) ابحث عن آخر try: على سطر مستقل
try_idx = None
for i, line in enumerate(src):
    if re.match(r"^\s*try:\s*$", line):
        try_idx = i

if try_idx is None:
    print("No line with 'try:' found — nothing to patch.")
else:
    try_indent = indent_of(src[try_idx])

    # 2) افحص إن كان هناك except/finally بنفس المستوى بعد هذا الـ try
    has_handler = False
    for j in range(try_idx + 1, len(src)):
        line = src[j]
        # إذا بدأنا كتلة جديدة/تعريف على نفس المستوى وغابت except/finally، نوقف الفحص
        if re.match(rf"^{re.escape(try_indent)}(def |class |@|if |for |while |with |try:|return|import |from |st\.)", line):
            break
        if re.match(rf"^{re.escape(try_indent)}(except\b|finally:)", line):
            has_handler = True
            break
    if not has_handler:
        # 3) تأكد أن كتلة الـ try تحتوي سطر جسم واحد على الأقل مباشرة بعدها
        # ابحث عن أول سطر غير فارغ بعد try
        k = try_idx + 1
        while k < len(src) and is_blank(src[k]):
            k += 1
        need_body_pass = True
        if k < len(src):
            # لو السطر التالي أكثر إزاحة من try_indent فهذا جسم صحيح
            need_body_pass = len(indent_of(src[k])) <= len(try_indent)

        # إدراج "    pass" بعد سطر try: لو مافيش جسم
        if need_body_pass:
            src.insert(try_idx + 1, try_indent + "    pass")

        # 4) أضف except في نهاية الكتلة قبل أي تعريف/كتلة جديدة على نفس المستوى
        insert_pos = len(src)
        for j in range(try_idx + 1, len(src)):
            line = src[j]
            # نقطة إدراج مع أول عودة لنفس مستوى الإزاحة أو بدء تعريف جديد
            if re.match(rf"^{re.escape(try_indent)}(def |class |@|if |for |while |with |try:|return|import |from )", line):
                insert_pos = j
                break
        handler = [
            try_indent + "except Exception as e:",
            try_indent + "    pass",
        ]
        src[insert_pos:insert_pos] = handler
        print(f"Patched dangling try: at line {try_idx+1}")

    else:
        print("Found handler already — nothing to patch.")

# 5) اكتب الملف
Path(p).write_text("\n".join(src) + ("\n" if src and src[-1] != "" else ""), encoding="utf-8")
