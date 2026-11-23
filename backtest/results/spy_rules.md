# S&P 500: hold vs get-out rules

Data: SPY with dividends, 1993-01-29 to 2026-11-23. Out = T-bills. Trades at the next day's open, 0.05% cost per switch. $1,000 at the start of each period.

## Since 1993 (33 years)

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $30,078 | +10.59% | -55.2% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $3,536 | +3.81% | -45.7% | 275 | 78% |
| Out at -4.5% from the high, back in at +3% from the low | $4,770 | +4.73% | -54.8% | 327 | 85% |
| Out at -4.5% from the high, back in after 3 up days in a row | $5,865 | +5.37% | -43.6% | 279 | 82% |
| Out after 3 down days totalling -3%, back after 3 up days | $10,689 | +7.26% | -54.6% | 225 | 86% |
| Bot's storm switch: 2 closes below / above the 200-day average | $21,603 | +9.51% | -19.8% | 119 | 78% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $24,406 | +9.91% | -26.7% | 32 | 84% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $20,112 | +9.28% | -24.2% | 48 | 82% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $22,753 | +9.68% | -23.2% | 52 | 81% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $20,478 | +9.34% | -20.6% | 105 | 77% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $13,587 | +8.02% | -17.3% | 53 | 68% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $20,728 | +9.38% | -18.0% | 73 | 74% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $20,585 | +9.36% | -18.6% | 91 | 76% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $19,046 | +9.11% | -17.7% | 59 | 72% |
| Out at -10% from the high, back in at +10% from the low | $29,464 | +10.52% | -38.0% | 53 | 87% |
| Out at -15% from the high, back in at +15% from the low | $16,444 | +8.63% | -47.3% | 30 | 91% |
| Out at -20% from the high, back in at +20% from the low | $30,946 | +10.68% | -48.3% | 12 | 93% |
| Out at -10% from the high, back in above the 200-day average | $22,769 | +9.68% | -23.9% | 43 | 84% |
| Out at -15% from the high, back in above the 200-day average | $20,571 | +9.35% | -36.5% | 22 | 87% |
| Out at -20% from the high, back in above the 200-day average | $32,089 | +10.80% | -37.7% | 10 | 91% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $46,902 | +12.05% | -27.5% | 73 | 74% |
| Half S&P + half 2x S&P, just hold (no switch) | $59,649 | +12.85% | -75.6% | 0 | 100% |
| 2x S&P, just hold (no switch) | $89,221 | +14.20% | -87.8% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $100,188 | +14.60% | -38.8% | 119 | 78% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $93,777 | +14.37% | -35.8% | 73 | 74% |
| 3x S&P, just hold (no switch) | $109,652 | +14.90% | -98.0% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $354,921 | +18.96% | -53.9% | 119 | 78% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $328,222 | +18.69% | -53.0% | 73 | 74% |

## Last 10 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $4,015 | +14.82% | -33.7% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $2,349 | +8.86% | -23.0% | 73 | 82% |
| Out at -4.5% from the high, back in at +3% from the low | $2,469 | +9.40% | -25.3% | 87 | 88% |
| Out at -4.5% from the high, back in after 3 up days in a row | $2,505 | +9.56% | -24.6% | 73 | 85% |
| Out after 3 down days totalling -3%, back after 3 up days | $3,123 | +11.99% | -28.2% | 65 | 88% |
| Bot's storm switch: 2 closes below / above the 200-day average | $3,012 | +11.58% | -17.9% | 35 | 84% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $2,743 | +10.55% | -26.7% | 10 | 89% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $2,598 | +9.96% | -20.6% | 16 | 87% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $2,867 | +11.04% | -23.2% | 16 | 86% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $3,151 | +12.09% | -17.4% | 29 | 83% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $2,607 | +10.00% | -17.3% | 17 | 78% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $3,024 | +11.63% | -17.1% | 23 | 82% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $3,096 | +11.89% | -18.4% | 27 | 83% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $2,973 | +11.44% | -14.9% | 19 | 81% |
| Out at -10% from the high, back in at +10% from the low | $4,181 | +15.28% | -25.7% | 15 | 89% |
| Out at -15% from the high, back in at +15% from the low | $2,920 | +11.24% | -30.6% | 10 | 91% |
| Out at -20% from the high, back in at +20% from the low | $3,391 | +12.91% | -26.7% | 4 | 90% |
| Out at -10% from the high, back in above the 200-day average | $2,841 | +10.94% | -23.7% | 15 | 88% |
| Out at -15% from the high, back in above the 200-day average | $2,852 | +10.98% | -20.9% | 8 | 90% |
| Out at -20% from the high, back in above the 200-day average | $3,242 | +12.40% | -26.7% | 4 | 93% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $4,279 | +15.55% | -26.5% | 23 | 82% |
| Half S&P + half 2x S&P, just hold (no switch) | $6,126 | +19.75% | -48.8% | 0 | 100% |
| 2x S&P, just hold (no switch) | $8,238 | +23.32% | -58.8% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $5,715 | +18.92% | -35.0% | 35 | 84% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $5,774 | +19.04% | -33.8% | 23 | 82% |
| 3x S&P, just hold (no switch) | $13,147 | +29.19% | -76.2% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $10,040 | +25.77% | -49.0% | 35 | 84% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $10,237 | +26.02% | -47.4% | 23 | 82% |

## Last 5 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,681 | +10.82% | -24.5% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $1,385 | +6.64% | -23.0% | 37 | 78% |
| Out at -4.5% from the high, back in at +3% from the low | $1,276 | +4.93% | -25.3% | 49 | 84% |
| Out at -4.5% from the high, back in after 3 up days in a row | $1,324 | +5.71% | -24.6% | 41 | 80% |
| Out after 3 down days totalling -3%, back after 3 up days | $1,340 | +5.96% | -28.2% | 35 | 85% |
| Bot's storm switch: 2 closes below / above the 200-day average | $1,447 | +7.58% | -17.9% | 23 | 78% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,405 | +6.96% | -20.5% | 6 | 85% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $1,289 | +5.14% | -20.6% | 10 | 82% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $1,422 | +7.21% | -23.2% | 10 | 82% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $1,465 | +7.83% | -17.4% | 19 | 77% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $1,360 | +6.26% | -11.9% | 11 | 70% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $1,431 | +7.34% | -17.1% | 15 | 76% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $1,433 | +7.37% | -18.4% | 19 | 77% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $1,451 | +7.64% | -14.3% | 13 | 74% |
| Out at -10% from the high, back in at +10% from the low | $1,629 | +10.12% | -25.7% | 9 | 89% |
| Out at -15% from the high, back in at +15% from the low | $1,197 | +3.62% | -30.6% | 6 | 86% |
| Out at -20% from the high, back in at +20% from the low | $1,509 | +8.47% | -21.3% | 2 | 81% |
| Out at -10% from the high, back in above the 200-day average | $1,350 | +6.12% | -23.7% | 9 | 84% |
| Out at -15% from the high, back in above the 200-day average | $1,420 | +7.18% | -20.9% | 4 | 87% |
| Out at -20% from the high, back in above the 200-day average | $1,583 | +9.50% | -24.6% | 2 | 91% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $1,487 | +8.16% | -25.9% | 15 | 76% |
| Half S&P + half 2x S&P, just hold (no switch) | $1,795 | +12.26% | -35.7% | 0 | 100% |
| 2x S&P, just hold (no switch) | $1,909 | +13.64% | -46.5% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $1,562 | +9.21% | -35.0% | 23 | 78% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,530 | +8.76% | -33.8% | 15 | 76% |
| 3x S&P, just hold (no switch) | $1,946 | +14.06% | -63.6% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $1,624 | +10.06% | -49.0% | 23 | 78% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,579 | +9.45% | -47.4% | 15 | 76% |

## Last 2 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,296 | +13.43% | -18.8% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $1,198 | +9.17% | -15.8% | 11 | 89% |
| Out at -4.5% from the high, back in at +3% from the low | $1,204 | +9.42% | -15.9% | 13 | 91% |
| Out at -4.5% from the high, back in after 3 up days in a row | $1,265 | +12.09% | -12.9% | 9 | 88% |
| Out after 3 down days totalling -3%, back after 3 up days | $1,233 | +10.72% | -18.3% | 9 | 94% |
| Bot's storm switch: 2 closes below / above the 200-day average | $1,170 | +7.92% | -11.5% | 7 | 89% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,087 | +4.13% | -20.5% | 2 | 95% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $1,025 | +1.23% | -20.5% | 4 | 93% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $1,169 | +7.89% | -11.5% | 4 | 92% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $1,203 | +9.40% | -11.5% | 5 | 89% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $1,112 | +5.31% | -11.5% | 5 | 82% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $1,191 | +8.87% | -11.5% | 5 | 89% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $1,191 | +8.87% | -11.5% | 5 | 89% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $1,168 | +7.83% | -11.5% | 5 | 88% |
| Out at -10% from the high, back in at +10% from the low | $1,355 | +15.89% | -12.2% | 3 | 96% |
| Out at -15% from the high, back in at +15% from the low | $1,090 | +4.30% | -20.3% | 2 | 95% |
| Out at -20% from the high, back in at +20% from the low | $1,296 | +13.43% | -18.8% | 0 | 100% |
| Out at -10% from the high, back in above the 200-day average | $1,045 | +2.15% | -23.7% | 5 | 93% |
| Out at -15% from the high, back in above the 200-day average | $1,082 | +3.93% | -20.9% | 2 | 95% |
| Out at -20% from the high, back in above the 200-day average | $1,296 | +13.43% | -18.8% | 0 | 100% |
| HALF S&P + HALF 2x S&P + switch (out at/below the 200-day, back in 2%+ above) | $1,219 | +10.10% | -17.3% | 5 | 89% |
| Half S&P + half 2x S&P, just hold (no switch) | $1,364 | +16.27% | -27.2% | 0 | 100% |
| 2x S&P, just hold (no switch) | $1,432 | +19.04% | -35.2% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $1,202 | +9.36% | -22.6% | 7 | 89% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,246 | +11.27% | -22.6% | 5 | 89% |
| 3x S&P, just hold (no switch) | $1,516 | +22.40% | -48.9% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $1,213 | +9.82% | -33.1% | 7 | 89% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,279 | +12.71% | -33.1% | 5 | 89% |

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

$1,000 from 2006-06-21: real SSO $16,857, simulated 2x $19,268.

