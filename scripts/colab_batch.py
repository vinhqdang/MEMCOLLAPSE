"""Executed on a Colab VM via `colab exec -f`. Runs a queue of repo commands in the background.

Set MC_JOBS (newline-separated commands, run from the repo root) by prepending
`import os; os.environ["MC_JOBS"] = "..."` to this file before exec. Each command's
output goes to logs/job_<k>.log; job.out records progress. Poll with colab_status_all.py.
"""
import os
import shlex
import subprocess

REPO = "https://github.com/vinhqdang/MEMCOLLAPSE.git"
WORK = "/content/MEMCOLLAPSE"
JOBS = [j.strip() for j in os.environ.get("MC_JOBS", "").splitlines() if j.strip()]
if not JOBS:
    raise SystemExit("MC_JOBS is empty")

if not os.path.isdir(WORK):
    subprocess.run(["git", "clone", "-q", REPO, WORK], check=True)
else:
    subprocess.run(["git", "-C", WORK, "pull", "-q"], check=True)
subprocess.run(["pip", "install", "-q", "-U", "transformers>=5.0", "accelerate"], check=True)

lines = [f"cd {WORK}", "mkdir -p logs"]
for k, job in enumerate(JOBS):
    lines.append(f"echo START {k}: {shlex.quote(job)}")
    lines.append(f"{job} > logs/job_{k}.log 2>&1 && echo OK {k} || echo FAILED {k}")
lines.append("echo ALL_DONE")
with open(f"{WORK}/job.sh", "w") as f:
    f.write("\n".join(lines) + "\n")
subprocess.Popen(f"nohup bash {WORK}/job.sh > {WORK}/job.out 2>&1 &", shell=True)
print(f"launched {len(JOBS)} jobs")
