# Distribution experiments

All rates are fictional. These trials test decisions, not ecological accuracy.

## V1: short establishment, cheap crew

24 six-month turns, crew 2, canopy growth up to 25 points per turn. The first
80-seed sweep tested public-information policies, not hidden-state optimisers.

| Distribution | Rush planting | Manual follow-up | Community care | Targeted information/care | Full protection |
|---|---:|---:|---:|---:|---:|
| Gentle | 48/80 | 80/80 | 80/80 | 80/80 | 80/80 |
| Varied | 1/80 | 79/80 | 80/80 | 80/80 | 80/80 |
| Severe | 0/80 | 64/80 | 70/80 | 80/80 | 80/80 |

Harvest-only never restored a target. It accumulated credits while health fell.
The mild/varied manual policy was already almost certain to finish. This left
little reason to buy information. Severe conditions made protection useful,
but finished canopies soon produced very large cash surpluses.

### Lower-cost CLI players

Claude CLI used `haiku`; Cursor CLI used `gpt-5.4-mini-low`. Neither received
source code or hidden variables. They used the same public view as the UI.

Claude first claimed victory after clearing three patches. Its actual target
count was zero. This run is a failure of understanding, not a win. It was told
explicitly that bare ground is not a closed canopy, then resumed. Its reported
trace replays to three closed targets, 90 credits, health 70 at the start of
turn 24. Its self-reported cash and turn totals were inaccurate.

```text
clear:east clear:edge clear:neck wait plant:neck plant:edge
buy:community:neck buy:community:edge tend:neck tend:edge clear:east
buy:mulch:edge plant:east buy:community:east tend:east tend:east tend:east
wait wait wait wait wait wait wait wait wait wait
```

Cursor stopped early at turn 13 with two targets, 21 credits and health 62.
East was slowed by grass, then burned after its firebreak expired. It wrongly
suggested becoming mixed forest had reduced the target count; mixed forest
does count. Its trace:

```text
clear:neck plant:neck buy:community:neck clear:edge plant:edge
buy:community:edge clear:middle clear:east buy:firebreak:east plant:east
wait wait wait wait wait
```

Changes motivated by this round: say bare ground explicitly, print the actual
win status, separate buying from advancing time, show expiry and causes, and
test a longer vulnerable period before deciding that every sensor is needed.
