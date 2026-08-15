# Freshness Checklist

The normative fields and conditionals are in
`contracts/coaching-contract.v1.schema.json`.

Before personalized coaching:

- read `get_planning_context` now;
- verify the accepted-state context revision;
- use each source's `sourceTime` and freshness status;
- verify target local date and IANA timezone;
- verify `activeSessionId` is present or explicitly `null`;
- separate phone-accepted state from agent proposal history;
- treat missing or provenance-free data as unknown.

`generatedAt` is only bundle assembly time. It cannot make an old phone event
fresh.

Do not claim live mid-set knowledge unless fresh phone provenance names the set
or event. Do not claim older history beyond the accepted planning window.

If freshness, provenance, or revision is missing, stop state-changing coaching.
Ask for a fresh sync or compatible runtime. Do not call undocumented snapshot,
memory, HealthKit, or daily-snapshot tools as a fallback.
