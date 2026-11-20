# S&P 500: hold vs get-out rules

Data: SPY with dividends, 1993-01-29 to 2026-11-19. Out = T-bills. Trades at the next day's open, 0.05% cost per switch. $1,000 at the start of each period.

## Since 1993 (33 years)

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $29,762 | +10.56% | -55.2% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $3,535 | +3.81% | -45.7% | 275 | 78% |
| Out at -4.5% from the high, back in at +3% from the low | $4,786 | +4.74% | -54.8% | 326 | 85% |
| Out at -4.5% from the high, back in after 3 up days in a row | $5,863 | +5.37% | -43.6% | 279 | 82% |
| Out after 3 down days totalling -3%, back after 3 up days | $10,686 | +7.26% | -54.6% | 225 | 86% |
| Bot's storm switch: 2 closes below / above the 200-day average | $21,358 | +9.48% | -19.8% | 118 | 78% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $24,150 | +9.88% | -26.7% | 32 | 84% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $19,901 | +9.25% | -24.2% | 48 | 82% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $22,514 | +9.65% | -23.2% | 52 | 81% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $20,246 | +9.31% | -20.6% | 104 | 77% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $13,433 | +7.99% | -17.3% | 52 | 68% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $20,493 | +9.35% | -18.0% | 72 | 74% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $20,351 | +9.32% | -18.6% | 90 | 76% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $18,830 | +9.07% | -17.7% | 58 | 72% |
| Out at -10% from the high, back in at +10% from the low | $29,130 | +10.49% | -38.0% | 52 | 87% |
| Out at -15% from the high, back in at +15% from the low | $16,271 | +8.60% | -47.3% | 30 | 91% |
| Out at -20% from the high, back in at +20% from the low | $30,621 | +10.65% | -48.3% | 12 | 93% |
| Out at -10% from the high, back in above the 200-day average | $22,510 | +9.65% | -23.9% | 42 | 84% |
| Out at -15% from the high, back in above the 200-day average | $20,355 | +9.32% | -36.5% | 22 | 87% |
| Out at -20% from the high, back in above the 200-day average | $31,752 | +10.77% | -37.7% | 10 | 91% |
| 2x S&P, just hold (no switch) | $87,705 | +14.15% | -87.8% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $98,296 | +14.54% | -38.8% | 118 | 78% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $92,007 | +14.31% | -35.8% | 72 | 74% |
| 3x S&P, just hold (no switch) | $107,455 | +14.84% | -98.0% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $346,795 | +18.89% | -53.9% | 118 | 78% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $320,711 | +18.61% | -53.0% | 72 | 74% |

## Last 10 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $3,973 | +14.72% | -33.7% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $2,348 | +8.87% | -23.0% | 73 | 82% |
| Out at -4.5% from the high, back in at +3% from the low | $2,477 | +9.45% | -25.3% | 86 | 88% |
| Out at -4.5% from the high, back in after 3 up days in a row | $2,504 | +9.57% | -24.6% | 73 | 85% |
| Out after 3 down days totalling -3%, back after 3 up days | $3,122 | +12.00% | -28.2% | 65 | 88% |
| Bot's storm switch: 2 closes below / above the 200-day average | $2,978 | +11.47% | -17.9% | 34 | 84% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $2,714 | +10.45% | -26.7% | 10 | 89% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $2,571 | +9.85% | -20.6% | 16 | 87% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $2,836 | +10.93% | -23.2% | 16 | 86% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $3,115 | +11.97% | -17.4% | 28 | 83% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $2,578 | +9.88% | -17.3% | 16 | 78% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $2,990 | +11.52% | -17.1% | 22 | 82% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $3,061 | +11.78% | -18.4% | 26 | 83% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $2,939 | +11.33% | -14.9% | 18 | 81% |
| Out at -10% from the high, back in at +10% from the low | $4,133 | +15.17% | -25.7% | 14 | 89% |
| Out at -15% from the high, back in at +15% from the low | $2,889 | +11.14% | -30.6% | 10 | 91% |
| Out at -20% from the high, back in at +20% from the low | $3,356 | +12.80% | -26.7% | 4 | 90% |
| Out at -10% from the high, back in above the 200-day average | $2,809 | +10.83% | -23.7% | 14 | 88% |
| Out at -15% from the high, back in above the 200-day average | $2,822 | +10.88% | -20.9% | 8 | 90% |
| Out at -20% from the high, back in above the 200-day average | $3,208 | +12.30% | -26.7% | 4 | 93% |
| 2x S&P, just hold (no switch) | $8,098 | +23.14% | -58.8% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $5,607 | +18.72% | -35.0% | 34 | 84% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $5,665 | +18.84% | -33.8% | 22 | 82% |
| 3x S&P, just hold (no switch) | $12,884 | +28.97% | -76.2% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $9,810 | +25.51% | -49.0% | 34 | 84% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $10,003 | +25.76% | -47.4% | 22 | 82% |

## Last 5 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,664 | +10.61% | -24.5% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $1,384 | +6.65% | -23.0% | 37 | 78% |
| Out at -4.5% from the high, back in at +3% from the low | $1,280 | +5.01% | -25.3% | 48 | 84% |
| Out at -4.5% from the high, back in after 3 up days in a row | $1,324 | +5.71% | -24.6% | 41 | 80% |
| Out after 3 down days totalling -3%, back after 3 up days | $1,340 | +5.97% | -28.2% | 35 | 85% |
| Bot's storm switch: 2 closes below / above the 200-day average | $1,431 | +7.35% | -17.9% | 22 | 78% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,391 | +6.75% | -20.5% | 6 | 85% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $1,275 | +4.93% | -20.6% | 10 | 82% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $1,407 | +7.00% | -23.2% | 10 | 82% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $1,448 | +7.61% | -17.4% | 18 | 77% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $1,344 | +6.03% | -11.9% | 10 | 70% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $1,415 | +7.11% | -17.1% | 14 | 76% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $1,417 | +7.14% | -18.4% | 18 | 77% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $1,435 | +7.41% | -14.3% | 12 | 74% |
| Out at -10% from the high, back in at +10% from the low | $1,610 | +9.89% | -25.7% | 8 | 89% |
| Out at -15% from the high, back in at +15% from the low | $1,185 | +3.42% | -30.6% | 6 | 86% |
| Out at -20% from the high, back in at +20% from the low | $1,493 | +8.26% | -21.3% | 2 | 81% |
| Out at -10% from the high, back in above the 200-day average | $1,335 | +5.89% | -23.7% | 8 | 84% |
| Out at -15% from the high, back in above the 200-day average | $1,405 | +6.97% | -20.9% | 4 | 87% |
| Out at -20% from the high, back in above the 200-day average | $1,566 | +9.29% | -24.6% | 2 | 91% |
| 2x S&P, just hold (no switch) | $1,877 | +13.28% | -46.5% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $1,532 | +8.82% | -35.0% | 22 | 78% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,501 | +8.37% | -33.8% | 14 | 76% |
| 3x S&P, just hold (no switch) | $1,907 | +13.64% | -63.6% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $1,587 | +9.58% | -49.0% | 22 | 78% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,543 | +8.97% | -47.4% | 14 | 76% |

## Last 2 years

| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |
|---|---|---|---|---|---|
| Just hold the S&P 500 | $1,283 | +12.92% | -18.8% | 0 | 100% |
| Your idea: out at -4.5% from the high, back in at +4.5% from the low | $1,198 | +9.20% | -15.8% | 11 | 89% |
| Out at -4.5% from the high, back in at +3% from the low | $1,208 | +9.66% | -15.9% | 12 | 92% |
| Out at -4.5% from the high, back in after 3 up days in a row | $1,265 | +12.14% | -12.9% | 9 | 89% |
| Out after 3 down days totalling -3%, back after 3 up days | $1,233 | +10.76% | -18.3% | 9 | 94% |
| Bot's storm switch: 2 closes below / above the 200-day average | $1,157 | +7.36% | -10.7% | 6 | 89% |
| Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it | $1,075 | +3.61% | -20.5% | 2 | 95% |
| Out after 2 closes 3% below the 200-day, back after 3 closes above it | $1,015 | +0.71% | -20.5% | 4 | 93% |
| Out after 2 closes 2% below the 200-day, back after 3 closes above it | $1,157 | +7.38% | -10.0% | 4 | 92% |
| Out after 2 closes below the 200-day, back after 3 closes above it | $1,189 | +8.84% | -9.3% | 4 | 89% |
| YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it | $1,100 | +4.75% | -9.3% | 4 | 82% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it | $1,178 | +8.32% | -9.3% | 4 | 89% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 1%+ above it | $1,178 | +8.32% | -9.3% | 4 | 89% |
| Out after 2 closes at/below the 200-day, back in after 2 closes 3%+ above it | $1,155 | +7.27% | -9.3% | 4 | 88% |
| Out at -10% from the high, back in at +10% from the low | $1,339 | +15.33% | -12.2% | 2 | 96% |
| Out at -15% from the high, back in at +15% from the low | $1,079 | +3.78% | -20.3% | 2 | 95% |
| Out at -20% from the high, back in at +20% from the low | $1,283 | +12.92% | -18.8% | 0 | 100% |
| Out at -10% from the high, back in above the 200-day average | $1,033 | +1.60% | -23.7% | 4 | 93% |
| Out at -15% from the high, back in above the 200-day average | $1,071 | +3.41% | -20.9% | 2 | 95% |
| Out at -20% from the high, back in above the 200-day average | $1,283 | +12.92% | -18.8% | 0 | 100% |
| 2x S&P, just hold (no switch) | $1,407 | +18.16% | -35.2% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $1,179 | +8.39% | -21.3% | 6 | 89% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,222 | +10.31% | -18.5% | 4 | 89% |
| 3x S&P, just hold (no switch) | $1,486 | +21.32% | -48.9% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $1,185 | +8.64% | -30.9% | 6 | 89% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $1,250 | +11.52% | -27.1% | 4 | 89% |

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
| 2x S&P, just hold (no switch) | $895 | -5.46% | -46.5% | 0 | 100% |
| 2x S&P + 200-day switch (2 closes below / above) | $871 | -6.70% | -35.0% | 16 | 56% |
| 2x S&P + switch: out at/below the 200-day, back in 2%+ above | $823 | -9.33% | -33.8% | 10 | 50% |
| 3x S&P, just hold (no switch) | $736 | -14.34% | -63.6% | 0 | 100% |
| 3x S&P + 200-day switch (2 closes below / above) | $767 | -12.48% | -49.0% | 16 | 56% |
| 3x S&P + switch: out at/below the 200-day, back in 2%+ above | $707 | -16.02% | -47.4% | 10 | 50% |

## Check: simulated 2x vs the real SSO fund

$1,000 from 2006-06-21: real SSO $16,584, simulated 2x $18,940.

