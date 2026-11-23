"""Executed on the Colab VM: print job progress and pack finished results."""
import glob
import os
import subprocess

WORK = "/content/MEMCOLLAPSE"
print(open(f"{WORK}/job.out").read()[-800:] if os.path.exists(f"{WORK}/job.out") else "no job.out")
for log in sorted(glob.glob(f"{WORK}/results/pilot/logs/*.log")):
    tail = [ln for ln in open(log, errors="ignore").read().splitlines()
            if "Loading weights" not in ln and "HTTP Request" not in ln][-2:]
    print(os.path.basename(log), "|", " / ".join(tail)[-300:])
subprocess.run(f"cd {WORK} && tar czf /content/pilot_results.tgz results/pilot", shell=True)
print(subprocess.run("nvidia-smi --query-gpu=name,memory.used,utilization.gpu --format=csv,noheader",
                     shell=True, capture_output=True, text=True).stdout)
