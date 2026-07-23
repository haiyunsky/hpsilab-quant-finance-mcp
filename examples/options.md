# Options and Volatility Prompts

## Volatility valuation

```text
Use HPSILab's IV radar for AAPL. Explain ATM IV, IV rank, IV percentile, volatility
regime, skew, and risk reversal in plain language. Conclude only whether volatility
appears low, normal, elevated, or extreme relative to the returned history—not
whether an option should be bought or sold.
```

## Positioning map

```text
Use HPSILab's option-pressure tool for TSLA. List max pain, gamma wall, expected
move, squeeze target, expiry date, and the most important pressure zones. Explain
why each level can matter and why none should be treated as a guaranteed target.
```

## Combined volatility and pressure brief

```text
Use get_iv_radar and get_option_pressure for QQQ. Produce a scenario table for
below, inside, and above the expected-move range. Incorporate IV regime and major
strike concentrations, but do not invent option Greeks or expiry data that were
not returned.
```

## Visual review

```text
Generate HPSILab images for SPY using only the iv_radar and option_pressure image
types. Ask before retrying because image generation is non-idempotent. Explain
what each returned URL represents and mention that hosted URLs can expire.
```

