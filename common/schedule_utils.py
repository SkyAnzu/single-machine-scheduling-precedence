from collections import deque


def window_tightening(job_count, ready_dates, durations, deadlines, successors):
    predecessors = {job: [] for job in range(1, job_count + 1)}
    for job in range(1, job_count + 1):
        for successor in successors[job]:
            predecessors[successor].append(job)

    indegree = {job: len(predecessors[job]) for job in range(1, job_count + 1)}
    queue = deque(job for job in range(1, job_count + 1) if indegree[job] == 0)
    topological_order = []

    while queue:
        job = queue.popleft()
        topological_order.append(job)
        for successor in successors[job]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)

    if len(topological_order) != job_count:
        raise ValueError("Precedence graph has a cycle!")

    tightened_ready_dates = {job: ready_dates[job] for job in range(1, job_count + 1)}
    for job in topological_order:
        if predecessors[job]:
            tightened_ready_dates[job] = max(
                ready_dates[job],
                max(tightened_ready_dates[parent] + durations[parent] for parent in predecessors[job]),
            )

    tightened_deadlines = {job: deadlines[job] for job in range(1, job_count + 1)}
    for job in reversed(topological_order):
        if successors[job]:
            tightened_deadlines[job] = min(
                tightened_deadlines[job],
                min(tightened_deadlines[successor] - durations[successor] for successor in successors[job]),
            )

    return tightened_ready_dates, tightened_deadlines


def compute_max_lateness(schedule, durations, due_dates, clamp_zero=False):
    if not schedule:
        return 0

    lateness_values = []
    for job, start_time in schedule.items():
        completion_time = start_time + durations[job]
        lateness = completion_time - due_dates[job]
        lateness_values.append(max(0, lateness) if clamp_zero else lateness)

    return max(lateness_values)


def validate_schedule(schedule, job_count, durations, ready_dates, deadlines, successors):
    violations = []

    for job in range(1, job_count + 1):
        if job not in schedule:
            violations.append(f"[C1] Job {job} is not scheduled")

    if violations:
        return False, violations

    if len(schedule) != job_count:
        violations.append(f"[C4] So job trong schedule ({len(schedule)}) != n ({job_count})")
        return False, violations

    for job, start_time in schedule.items():
        if job not in durations:
            violations.append(f"[C2] Job {job} is missing from the instance data")
            continue

        completion_time = start_time + durations[job]
        if start_time < ready_dates[job]:
            violations.append(f"[C2] Job {job}: start={start_time} < ready_date={ready_dates[job]}")
        if completion_time > deadlines[job]:
            violations.append(f"[C2] Job {job}: end={completion_time} > deadline={deadlines[job]}")

    intervals = []
    for job, start_time in schedule.items():
        intervals.append((start_time, start_time + durations[job], job))
    intervals.sort()

    for index in range(len(intervals) - 1):
        start_a, end_a, job_a = intervals[index]
        start_b, end_b, job_b = intervals[index + 1]
        if end_a > start_b:
            violations.append(
                f"[C3] Overlap: Job {job_a} [{start_a}, {end_a}) va Job {job_b} [{start_b}, {end_b})"
            )

    for job in range(1, job_count + 1):
        finish_time = schedule[job] + durations[job]
        for successor in successors[job]:
            if successor not in schedule:
                violations.append(f"[C5] Job {job} has successor {successor}, but job {successor} is not scheduled")
                continue
            if finish_time > schedule[successor]:
                violations.append(
                    f"[C5] Precedence violation: {job} -> {successor}, but finish({job})={finish_time} > start({successor})={schedule[successor]}"
                )

    return len(violations) == 0, violations
