import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "tools")
import gazetteer  # noqa: E402

g = gazetteer.gazetteer()
print(len(g.by_name), "noms indexes")
tests = [
    "Mali : reprise des negociations a Bamako",
    "Le Maroc face a la menace terroriste",
    "Germany's economy slows as China exports fall",
    "El presidente de Paraguay dimite",
    "Guerra in Ucraina, nuovi colloqui",
    "ارتفاع أسعار النفط في الجزائر",
    "Cristiano Ronaldo tourne la page de la selection",
]
for t in tests:
    print("  " + t[:46].ljust(48), [(x["iso"], x["region"]) for x in g.tag(t)])
