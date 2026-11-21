# S&P 500: hold vs get-out rules

Data: SPY with dividends, 1993-01-29 to 2026-11-20. Out = T-bills. Trades at the next day's open, 0.05% cost per switch. $1,000 at the start of each period.

## Since 1993 (33 years)

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $28,678 | +10.44% | -55.2% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $3,536 | +3.81% | -45.7% | 275 | 78% |
| Out at -4.5% from the high, back in at +3% from the low | $4,769 | +4.73% | -54.8% | 327 | 85% |
| Out at -4.5% from the high, back in after 3 up days in a row | $5,864 | +5.37% | -43.6% | 279 | 82% |
| Out after 3 down days totalling -3%, back after 3 up days | $10,688 | +7.26% | -54.6% | 225 | 86% |
| Bot's storm switch: 2 closes below / above the 200-day average | $20,581 | +9.36% | -19.8% | 118 | 78% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $23,271 | +9.76% | -26.7% | 32 | 84% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $19,177 | +9.13% | -24.2% | 48 | 82% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $21,695 | +9.53% | -23.2% | 52 | 81% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $19,509 | +9.19% | -20.6% | 104 | 77% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $12,944 | +7.87% | -17.3% | 52 | 68% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $19,747 | +9.22% | -18.0% | 72 | 74% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $19,610 | +9.20% | -18.6% | 90 | 76% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $18,145 | +8.95% | -17.7% | 58 | 72% |
| Out at -10% from the high, back in at +10% from the low | $28,069 | +10.37% | -38.0% | 52 | 87% |
| Out at -15% from the high, back in at +15% from the low | $15,679 | +8.48% | -47.3% | 30 | 91% |
| Out at -20% from the high, back in at +20% from the low | $29,506 | +10.53% | -48.3% | 12 | 93% |
| Out at -10% from the high, back in above the 200-day average | $21,691 | +9.53% | -23.9% | 42 | 84% |
| Out at -15% from the high, back in above the 200-day average | $19,614 | +9.20% | -36.5% | 22 | 87% |
| Out at -20% from the high, back in above the 200-day average | $30,596 | +10.65% | -37.7% | 10 | 91% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $43,660 | +11.82% | -27.5% | 72 | 74% |
| Half S&P + half 2x S&P, just hold (no switch) | $54,990 | +12.58% | -75.6% | 0 | 100% |
| 2x S&P, just hold (no switch) | $81,302 | +13.89% | -87.8% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $91,120 | +14.28% | -38.8% | 118 | 78% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $85,291 | +14.06% | -35.8% | 72 | 74% |
| 3x S&P, just hold (no switch) | $95,681 | +14.44% | -98.0% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $308,796 | +18.48% | -53.9% | 118 | 78% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $285,571 | +18.21% | -53.0% | 72 | 74% |

## Last 10 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $3,828 | +14.29% | -33.7% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $2,348 | +8.87% | -23.0% | 73 | 82% |
| Out at -4.5% from the high, back in at +3% from the low | $2,468 | +9.41% | -25.3% | 87 | 88% |
| Out at -4.5% from the high, back in after 3 up days in a row | $2,505 | +9.57% | -24.6% | 73 | 85% |
| Out after 3 down days totalling -3%, back after 3 up days | $3,123 | +12.00% | -28.2% | 65 | 88% |
| Bot's storm switch: 2 closes below / above the 200-day average | $2,869 | +11.06% | -17.9% | 34 | 84% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $2,615 | +10.04% | -26.7% | 10 | 89% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $2,477 | +9.45% | -20.6% | 16 | 87% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $2,733 | +10.52% | -23.2% | 16 | 86% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $3,002 | +11.56% | -17.4% | 28 | 83% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $2,484 | +9.47% | -17.3% | 16 | 78% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $2,881 | +11.10% | -17.1% | 22 | 82% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $2,949 | +11.36% | -18.4% | 26 | 83% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $2,832 | +10.91% | -14.9% | 18 | 81% |
| Out at -10% from the high, back in at +10% from the low | $3,983 | +14.74% | -25.7% | 14 | 89% |
| Out at -15% from the high, back in at +15% from the low | $2,784 | +10.72% | -30.6% | 10 | 91% |
| Out at -20% from the high, back in at +20% from the low | $3,234 | +12.39% | -26.7% | 4 | 90% |
| Out at -10% from the high, back in above the 200-day average | $2,707 | +10.41% | -23.7% | 14 | 88% |
| Out at -15% from the high, back in above the 200-day average | $2,720 | +10.47% | -20.9% | 8 | 90% |
| Out at -20% from the high, back in above the 200-day average | $3,091 | +11.88% | -26.7% | 4 | 93% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $3,983 | +14.74% | -26.5% | 22 | 82% |
| Half S&P + half 2x S&P, just hold (no switch) | $5,667 | +18.84% | -48.8% | 0 | 100% |
| 2x S&P, just hold (no switch) | $7,506 | +22.21% | -58.8% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $5,198 | +17.82% | -35.0% | 34 | 84% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $5,252 | +17.94% | -33.8% | 22 | 82% |
| 3x S&P, just hold (no switch) | $11,472 | +27.48% | -76.2% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $8,735 | +24.07% | -49.0% | 34 | 84% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $8,907 | +24.31% | -47.4% | 22 | 82% |

## Last 5 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,603 | +9.79% | -24.5% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $1,384 | +6.65% | -23.0% | 37 | 78% |
| Out at -4.5% from the high, back in at +3% from the low | $1,276 | +4.94% | -25.3% | 49 | 84% |
| Out at -4.5% from the high, back in after 3 up days in a row | $1,324 | +5.71% | -24.6% | 41 | 80% |
| Out after 3 down days totalling -3%, back after 3 up days | $1,340 | +5.97% | -28.2% | 35 | 85% |
| Bot's storm switch: 2 closes below / above the 200-day average | $1,379 | +6.56% | -17.9% | 22 | 78% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,340 | +5.96% | -20.5% | 6 | 85% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $1,229 | +4.16% | -20.6% | 10 | 82% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $1,356 | +6.21% | -23.2% | 10 | 82% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $1,395 | +6.82% | -17.4% | 18 | 77% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $1,295 | +5.25% | -11.9% | 10 | 70% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $1,363 | +6.33% | -17.1% | 14 | 76% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $1,365 | +6.35% | -18.4% | 18 | 77% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $1,383 | +6.62% | -14.3% | 12 | 74% |
| Out at -10% from the high, back in at +10% from the low | $1,551 | +9.08% | -25.7% | 8 | 89% |
| Out at -15% from the high, back in at +15% from the low | $1,142 | +2.66% | -30.6% | 6 | 86% |
| Out at -20% from the high, back in at +20% from the low | $1,439 | +7.46% | -21.3% | 2 | 81% |
| Out at -10% from the high, back in above the 200-day average | $1,286 | +5.11% | -23.7% | 8 | 84% |
| Out at -15% from the high, back in above the 200-day average | $1,354 | +6.19% | -20.9% | 4 | 87% |
| Out at -20% from the high, back in above the 200-day average | $1,509 | +8.49% | -24.6% | 2 | 91% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $1,384 | +6.65% | -25.9% | 14 | 76% |
| Half S&P + half 2x S&P, just hold (no switch) | $1,672 | +10.71% | -35.7% | 0 | 100% |
| 2x S&P, just hold (no switch) | $1,740 | +11.59% | -46.5% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $1,420 | +7.19% | -35.0% | 22 | 78% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,391 | +6.75% | -33.8% | 14 | 76% |
| 3x S&P, just hold (no switch) | $1,698 | +11.05% | -63.6% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $1,413 | +7.09% | -49.0% | 22 | 78% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,374 | +6.49% | -47.4% | 14 | 76% |

## Last 2 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,236 | +10.88% | -18.8% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $1,198 | +9.20% | -15.8% | 11 | 89% |
| Out at -4.5% from the high, back in at +3% from the low | $1,204 | +9.45% | -15.9% | 13 | 91% |
| Out at -4.5% from the high, back in after 3 up days in a row | $1,265 | +12.14% | -12.9% | 9 | 88% |
| Out after 3 down days totalling -3%, back after 3 up days | $1,233 | +10.76% | -18.3% | 9 | 94% |
| Bot's storm switch: 2 closes below / above the 200-day average | $1,114 | +5.43% | -11.5% | 6 | 90% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,036 | +1.75% | -20.5% | 2 | 95% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $978 | -1.09% | -20.5% | 4 | 93% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $1,115 | +5.45% | -11.5% | 4 | 92% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $1,146 | +6.88% | -11.5% | 4 | 89% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $1,060 | +2.87% | -11.5% | 4 | 83% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $1,135 | +6.36% | -11.5% | 4 | 89% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $1,135 | +6.36% | -11.5% | 4 | 89% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $1,113 | +5.34% | -11.5% | 4 | 88% |
| Out at -10% from the high, back in at +10% from the low | $1,291 | +13.25% | -12.2% | 2 | 96% |
| Out at -15% from the high, back in at +15% from the low | $1,040 | +1.92% | -20.3% | 2 | 95% |
| Out at -20% from the high, back in at +20% from the low | $1,236 | +10.88% | -18.8% | 0 | 100% |
| Out at -10% from the high, back in above the 200-day average | $995 | -0.22% | -23.7% | 4 | 93% |
| Out at -15% from the high, back in above the 200-day average | $1,032 | +1.55% | -20.9% | 2 | 95% |
| Out at -20% from the high, back in above the 200-day average | $1,236 | +10.88% | -18.8% | 0 | 100% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $1,135 | +6.36% | -17.3% | 4 | 89% |
| Half S&P + half 2x S&P, just hold (no switch) | $1,270 | +12.37% | -27.2% | 0 | 100% |
| 2x S&P, just hold (no switch) | $1,305 | +13.85% | -35.2% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $1,093 | +4.45% | -22.6% | 6 | 90% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,133 | +6.29% | -22.6% | 4 | 89% |
| 3x S&P, just hold (no switch) | $1,323 | +14.62% | -48.9% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $1,055 | +2.65% | -33.1% | 6 | 90% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,113 | +5.36% | -33.1% | 4 | 89% |

## 2008 crash (Oct 2007 - Mar 2013)

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,143 | +2.47% | -55.2% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $812 | -3.72% | -44.5% | 68 | 72% |
| Out at -4.5% from the high, back in at +3% from the low | $709 | -6.07% | -54.3% | 86 | 81% |
| Out at -4.5% from the high, back in after 3 up days in a row | $914 | -1.62% | -42.9% | 64 | 74% |
| Out after 3 down days totalling -3%, back after 3 up days | $902 | -1.85% | -51.0% | 56 | 77% |
| Bot's storm switch: 2 closes below / above the 200-day average | $1,277 | +4.56% | -18.8% | 28 | 62% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,246 | +4.09% | -21.1% | 10 | 68% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $1,161 | +2.75% | -24.2% | 14 | 66% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $1,225 | +3.77% | -19.4% | 16 | 64% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $1,322 | +5.22% | -17.9% | 22 | 60% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $1,359 | +5.74% | -11.8% | 9 | 51% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $1,469 | +7.26% | -14.4% | 10 | 58% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $1,356 | +5.70% | -16.8% | 18 | 60% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $1,466 | +7.21% | -11.7% | 8 | 57% |
| Out at -10% from the high, back in at +10% from the low | $1,337 | +5.43% | -38.0% | 14 | 78% |
| Out at -15% from the high, back in at +15% from the low | $1,026 | +0.48% | -40.9% | 10 | 74% |
| Out at -20% from the high, back in at +20% from the low | $1,412 | +6.49% | -35.5% | 4 | 91% |
| Out at -10% from the high, back in above the 200-day average | $1,376 | +5.98% | -23.9% | 8 | 72% |
| Out at -15% from the high, back in above the 200-day average | $1,021 | +0.39% | -36.5% | 8 | 76% |
| Out at -20% from the high, back in above the 200-day average | $1,449 | +7.00% | -25.7% | 2 | 84% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $1,687 | +10.00% | -21.9% | 10 | 58% |
| Half S&P + half 2x S&P, just hold (no switch) | $996 | -0.08% | -69.8% | 0 | 100% |
| 2x S&P, just hold (no switch) | $848 | -2.95% | -84.2% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $1,449 | +6.99% | -34.6% | 28 | 62% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,917 | +12.58% | -28.9% | 10 | 58% |
| 3x S&P, just hold (no switch) | $460 | -13.17% | -95.5% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $1,573 | +8.60% | -47.7% | 28 | 62% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $2,405 | +17.33% | -41.3% | 10 | 58% |

## 2020 Covid crash (2020)

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,172 | +17.30% | -33.7% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $997 | -0.31% | -21.9% | 20 | 75% |
| Out at -4.5% from the high, back in at +3% from the low | $1,029 | +2.93% | -23.1% | 20 | 83% |
| Out at -4.5% from the high, back in after 3 up days in a row | $1,083 | +8.29% | -13.0% | 14 | 77% |
| Out after 3 down days totalling -3%, back after 3 up days | $1,326 | +32.71% | -11.0% | 10 | 84% |
| Bot's storm switch: 2 closes below / above the 200-day average | $1,140 | +14.07% | -13.1% | 2 | 76% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,013 | +1.30% | -26.7% | 2 | 79% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $1,081 | +8.11% | -18.9% | 2 | 78% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $1,081 | +8.11% | -18.9% | 2 | 78% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $1,148 | +14.90% | -12.5% | 2 | 75% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $1,085 | +8.48% | -17.3% | 2 | 73% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $1,133 | +13.36% | -13.6% | 2 | 75% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $1,148 | +14.90% | -12.5% | 2 | 75% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $1,117 | +11.69% | -14.9% | 2 | 74% |
| Out at -10% from the high, back in at +10% from the low | $1,348 | +34.89% | -15.9% | 2 | 92% |
| Out at -15% from the high, back in at +15% from the low | $1,309 | +30.98% | -18.9% | 2 | 95% |
| Out at -20% from the high, back in at +20% from the low | $1,104 | +10.40% | -26.7% | 2 | 92% |
| Out at -10% from the high, back in above the 200-day average | $1,104 | +10.42% | -15.9% | 2 | 75% |
| Out at -15% from the high, back in above the 200-day average | $1,088 | +8.84% | -18.9% | 2 | 78% |
| Out at -20% from the high, back in above the 200-day average | $1,006 | +0.57% | -26.7% | 2 | 79% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $1,191 | +19.14% | -20.0% | 2 | 75% |
| Half S&P + half 2x S&P, just hold (no switch) | $1,191 | +19.14% | -46.5% | 0 | 100% |
| 2x S&P, just hold (no switch) | $1,209 | +20.99% | -58.8% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $1,253 | +25.39% | -25.2% | 2 | 76% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,238 | +23.87% | -26.1% | 2 | 75% |
| 3x S&P, just hold (no switch) | $1,112 | +11.27% | -76.2% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $1,347 | +34.87% | -36.3% | 2 | 76% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,323 | +32.43% | -37.4% | 2 | 75% |

## 2022 bear market (2022-2023)

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,026 | +1.33% | -24.5% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $953 | -2.42% | -23.0% | 22 | 60% |
| Out at -4.5% from the high, back in at +3% from the low | $839 | -8.44% | -25.3% | 32 | 72% |
| Out at -4.5% from the high, back in after 3 up days in a row | $847 | -8.05% | -24.6% | 28 | 66% |
| Out after 3 down days totalling -3%, back after 3 up days | $889 | -5.78% | -28.2% | 24 | 68% |
| Bot's storm switch: 2 closes below / above the 200-day average | $979 | -1.07% | -17.9% | 16 | 56% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,023 | +1.16% | -20.1% | 4 | 68% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $995 | -0.28% | -20.6% | 6 | 62% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $962 | -1.92% | -23.2% | 6 | 62% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $963 | -1.86% | -17.4% | 14 | 54% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $967 | -1.66% | -11.9% | 6 | 43% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $951 | -2.52% | -17.1% | 10 | 50% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $952 | -2.46% | -18.4% | 14 | 53% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $983 | -0.84% | -14.3% | 8 | 48% |
| Out at -10% from the high, back in at +10% from the low | $951 | -2.49% | -25.7% | 6 | 75% |
| Out at -15% from the high, back in at +15% from the low | $869 | -6.84% | -30.6% | 4 | 70% |
| Out at -20% from the high, back in at +20% from the low | $921 | -4.06% | -21.3% | 2 | 51% |
| Out at -10% from the high, back in above the 200-day average | $1,023 | +1.13% | -20.2% | 4 | 66% |
| Out at -15% from the high, back in above the 200-day average | $1,038 | +1.91% | -19.0% | 2 | 71% |
| Out at -20% from the high, back in above the 200-day average | $966 | -1.71% | -24.6% | 2 | 76% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $887 | -5.87% | -25.8% | 10 | 50% |
| Half S&P + half 2x S&P, just hold (no switch) | $961 | -2.01% | -35.5% | 0 | 100% |
| 2x S&P, just hold (no switch) | $895 | -5.46% | -46.5% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $871 | -6.70% | -35.0% | 16 | 56% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $823 | -9.33% | -33.8% | 10 | 50% |
| 3x S&P, just hold (no switch) | $736 | -14.34% | -63.6% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $767 | -12.48% | -49.0% | 16 | 56% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $707 | -16.02% | -47.4% | 10 | 50% |

## Check: simulated 2x vs the real SSO fund

$1,000 from 2006-06-21: real SSO $15,410, simulated 2x $17,558.

