"""Executed on a Colab VM via `colab exec -f scripts/colab_launch.py`.

Clones the public repo, upgrades transformers, and starts the pilot for the
given models in a detached background process so that a dropped websocket does
not kill the job. Poll with scripts/colab_status.py, then download results.
"""
import os
import subprocess

REPO = "https://github.com/vinhqdang/MEMCOLLAPSE.git"
WORK = "/content/MEMCOLLAPSE"
MODELS = os.environ.get("MC_MODELS", "google/gemma-4-E4B-it Qwen/Qwen2.5-7B-Instruct").split()
BATCH = os.environ.get("MC_BATCH", "24")

if not os.path.isdir(WORK):
    subprocess.run(["git", "clone", "-q", REPO, WORK], check=True)
else:
    subprocess.run(["git", "-C", WORK, "pull", "-q"], check=True)
subprocess.run(["pip", "install", "-q", "-U", "transformers>=5.0", "accelerate"], check=True)

lines = ["set -x", f"cd {WORK}", "mkdir -p results/pilot/logs"]
for m in MODELS:
    tag = m.split("/")[-1]
    lines.append(
        f"python scripts/run_pilot.py --model {m} --n 48 --sessions 16 --budgets 80 160 "
        f"--batch-size {BATCH} --out results/pilot > results/pilot/logs/{tag}.log 2>&1 "
        f"|| echo FAILED {m}"
    )
lines.append("echo ALL_DONE")
with open(f"{WORK}/job.sh", "w") as f:
    f.write("\n".join(lines) + "\n")
subprocess.Popen(f"nohup bash {WORK}/job.sh > {WORK}/job.out 2>&1 &", shell=True)
print("launched:", MODELS)
