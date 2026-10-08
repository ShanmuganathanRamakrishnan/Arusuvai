"""The same check as probe_ranker_live.py, with a reason-first prompt. (TASKS_3.md N13)

The model writes a short reason per plate before it names one -- often
better for small models. The prompt names no ingredient, so the soya count
below is not the prompt's own words coming back. Reads the cases file
probe_ranker_live.py wrote; writes the replies, reasons included.

    PYTHONPATH=. python docs/design/probes/probe_ranker_reason.py CASES.json OUT.json
"""
import json, sys, time, urllib.request, statistics
sys.path.insert(0, ".")
from llm.ranker import LETTERS, build_prompt, parse_choice
SYSTEM = ("You help plan Indian home meals. Every plate offered already meets the person's nutrition "
          "needs, and the amounts are fixed: do not judge or change amounts. Choose the one plate a family "
          "from the region would most naturally serve together as this meal. First, in 'reason', note for "
          "each plate in a few words whether its dishes are usually eaten together and whether any main "
          "ingredient appears in more than one dish. Then give the chosen plate's letter in 'plate'.")
cases = json.load(open(sys.argv[1]))
out = []
for c in cases:
    plates = [tuple(p) for p in c["plates"]]
    letters = list(LETTERS[:len(plates)])
    case_name = c["case"].split()
    region, meal = case_name[2], case_name[3]
    body = {"model": "qwen2.5:7b-instruct", "stream": False, "keep_alive": "30m",
            "options": {"temperature": 0, "seed": 0},
            "format": {"type": "object", "properties": {"reason": {"type": "string"},
                       "plate": {"type": "string", "enum": letters}}, "required": ["reason", "plate"]},
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": build_prompt(region, meal, plates)}]}
    t = time.perf_counter()
    r = json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=120))
    ch = parse_choice(r["message"]["content"], len(plates))
    out.append(dict(c, choice=ch, seconds=round(time.perf_counter() - t, 2), reply=r["message"]["content"]))
json.dump(out, open(sys.argv[2], "w"), indent=1)
soy = lambda p: sum("Soya" in d for d in p)
ok = [x for x in out if x["choice"] is not None]
print("cases", len(out), "no answer", len(out) - len(ok), "chose A", sum(x["choice"] == 0 for x in ok),
      "seconds median", statistics.median(x["seconds"] for x in out), "max", max(x["seconds"] for x in out))
print("soya dishes: nearest", sum(soy(x["plates"][0]) for x in ok), "model", sum(soy(x["plates"][x["choice"]]) for x in ok))
print("model more soya than nearest", sum(soy(x["plates"][x["choice"]]) > soy(x["plates"][0]) for x in ok),
      "fewer", sum(soy(x["plates"][x["choice"]]) < soy(x["plates"][0]) for x in ok))
