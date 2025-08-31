
AR_NUMS = "٠١٢٣٤٥٦٧٨٩"
EN_NUMS = "0123456789"
TRANS = str.maketrans(AR_NUMS, EN_NUMS)

def normalize_digits(s: str) -> str:
    return s.translate(TRANS)

MONTHS_AR = {"يناير":"01","فبراير":"02","مارس":"03","أبريل":"04","ابريل":"04","مايو":"05","يونيو":"06","يوليو":"07","أغسطس":"08","اغسطس":"08","سبتمبر":"09","أكتوبر":"10","اكتوبر":"10","نوفمبر":"11","ديسمبر":"12"}

MONTHS_DE = {
    "januar":"01","jan.":"01","jan":"01",
    "februar":"02","feb.":"02","feb":"02",
    "märz":"03","maerz":"03","mrz.":"03","mrz":"03","marz":"03",
    "april":"04","apr.":"04","apr":"04",
    "mai":"05",
    "juni":"06","jun.":"06","jun":"06",
    "juli":"07","jul.":"07","jul":"07",
    "august":"08","aug.":"08","aug":"08",
    "september":"09","sept.":"09","sep.":"09","sep":"09","sept":"09",
    "oktober":"10","okt.":"10","okt":"10",
    "november":"11","nov.":"11","nov":"11",
    "dezember":"12","dez.":"12","dez":"12"
}
