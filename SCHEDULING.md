# Local daily indexing

The scheduler starts a finite Python program. FastAPI runs separately.
This currently indexes an existing **complete** chunks JSON; it does not fetch
documents, extract them, or implement CK-14. Never supply only changed chunks:
the existing store replaces the entire corpus. The authoritative flag is an
operator assertion, not automatic verification that extraction is complete.

From this code directory, run manually with the project's Python environment:

```powershell
python -m app.jobs.daily_index --chunks 'D:\data\complete-chunks.json' --authoritative
```

Register a daily Windows task (example time and paths; replace them):

```powershell
.\scripts\register-daily-index.ps1 -Python 'D:\alarm system\code\.venv\Scripts\python.exe' -Chunks 'D:\data\complete-chunks.json' -At '02:00'
```

The time uses the Windows machine's local timezone. The task runs as the
current user while that user is logged in; locking the screen is fine, logging
out is not. The PC must be awake and have source access. StartWhenAvailable
allows a missed run to start later. IgnoreNew prevents overlapping executions
of this registered task, but does not lock out manually launched processes.
The task has a six-hour execution limit; tune it for the workload.

Run history is written atomically to `.state/runs/<run-id>.json`, with UTC
timestamps, status and results or errors. Exit 0 means success; exit 1 means
failure. If killed, a run can remain marked running; no failure alert or
missing-run monitor is implemented. Restrict access to logs as errors may
contain source details. Run records currently have no automatic retention.

Inspect or remove the task:

```powershell
Get-ScheduledTaskInfo -TaskName 'AlarmSystem-DailyIndex'
Unregister-ScheduledTask -TaskName 'AlarmSystem-DailyIndex'
```

For Azure Container Apps Jobs later, package this code and its dependencies
in a container and use the same `python -m app.jobs.daily_index` command with
the appropriate arguments. Configure the schedule and timeout in Azure.
Replace local input/state with durable mounted storage or a durable service;
add a distributed lease before allowing multiple launchers. No Azure job or
container image is deployed by these scripts. CK-14 specifies Azure Functions;
if that remains the agreed target, a timer function can invoke the same core
processing instead.
