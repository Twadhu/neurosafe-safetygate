# Safety and security policy

NeuroSafe SafetyGate is an educational research prototype. It is not approved for medical,
clinical, safety-critical, or unsupervised physical operation.

## Do not use this repository to

- Control a wheelchair, vehicle, industrial robot, or medical device around people.
- Collect human EEG data without institutional approval and informed consent.
- Treat synthetic simulation metrics as evidence of real-world safety.
- Remove an independent hardware emergency stop from a physical prototype.

## Before physical testing

1. Complete simulation acceptance tests and document failure cases.
2. Add a hardware emergency stop independent of the AI and main computer.
3. Add local obstacle stopping that remains active when communication fails.
4. Limit speed, power, test area, and access.
5. Use supervised testing with a written risk assessment.
6. Obtain all required institutional and ethics approvals.

Report software vulnerabilities privately to the repository owner. Do not include participant data,
credentials, private EEG recordings, or exploit details in a public issue.

