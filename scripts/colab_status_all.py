"""Executed on the Colab VM: print queue progress and pack results/ + data/rendered/."""
import glob
import os
import subprocess

WORK = "/content/MEMCOLLAPSE"
out = f"{WORK}/job.out"
print(open(out).read()[-600:] if os.path.exists(out) else "no job.out")
for log in sorted(glob.glob(f"{WORK}/logs/job_*.log")):
    tail = [ln for ln in open(log, errors="ignore").read().splitlines()
            if "Loading weights" not in ln and "HTTP Request" not in ln and ln.strip()][-1:]
    print(os.path.basename(log), "|", " ".join(tail)[-200:])
subprocess.run(f"cd {WORK} && tar czf /content/results.tgz --exclude='*.jsonl.gz' "
               f"results data/rendered 2>/dev/null", shell=True)
print(subprocess.run("nvidia-smi --query-gpu=name,memory.used,utilization.gpu --format=csv,noheader",
                     shell=True, capture_output=True, text=True).stdout)
