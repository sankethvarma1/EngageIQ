# SLA Policy

## Response Time SLAs
- Critical (P1): 1 hour initial response, 4 hour resolution target
- High (P2): 4 hour initial response, 24 hour resolution target
- Medium (P3): 8 hour initial response, 72 hour resolution target
- Low (P4): 24 hour initial response, 5 business day resolution target

## Availability SLAs
- Production systems: 99.9% uptime (monthly)
- Development environments: 99.0% uptime (monthly)
- Scheduled maintenance windows: Sunday 00:00-04:00 UTC

## Breach Consequences
- First breach in month: Formal notification to client
- Second breach: Service credit of 5% of monthly fee
- Third breach: Service credit of 15% of monthly fee + root cause analysis
- Chronic breaches (>3/month for 3 consecutive months): Contract renegotiation trigger

## Measurement
SLAs measured from ticket creation to resolution confirmation.
Business hours: Monday-Friday 09:00-18:00 local time.
Exclusions: Force majeure, client-caused delays, scheduled maintenance.