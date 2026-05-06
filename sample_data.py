"""
sample_data.py — Pre-written demo articles for the "Load Sample Data" button.

Topic: Federal Minimum Wage Increase Proposal

Three articles with clearly different framing, tone, and loaded language so
the bias-analysis features are immediately visible on first demo.
  - Wall Street Journal style → Economic / business framing, cautionary tone
  - The Guardian style       → Human interest framing, urgent/moral tone
  - Reuters style            → Neutral wire-service reporting, data-focused
"""

SAMPLE_TOPIC = "Federal Minimum Wage Increase Proposal"

SAMPLE_ARTICLES = [
    {
        "source": "Wall Street Journal",
        "text": (
            "Proposed Minimum Wage Hike Sparks Business Alarm\n\n"
            "Washington — A sweeping proposal to raise the federal minimum wage to $17 per hour "
            "by 2026 is drawing fierce opposition from small business owners and economists, who "
            "warn the legislation could trigger widespread job losses across vulnerable industries.\n\n"
            "The bill, advanced by Senate Democrats last week, would phase in the increase over "
            "three years, starting at $13 per hour and reaching the full amount by 2026. Proponents "
            "argue the raise is essential to help low-wage workers keep pace with inflation. But "
            "critics contend the rapid timeline leaves businesses — particularly in the restaurant, "
            "retail, and agriculture sectors — too little time to adjust their cost structures.\n\n"
            "The National Federation of Independent Business called the proposal 'economically "
            "reckless,' estimating it could eliminate up to 1.4 million jobs nationwide, with "
            "disproportionate losses in rural and lower-cost-of-living states. In Mississippi and "
            "Alabama, where median wages already sit close to the proposed floor, small operators "
            "say the arithmetic simply does not work.\n\n"
            "'You cannot legislate prosperity,' said James Harmon, who owns three franchise "
            "restaurants in rural Tennessee. 'If my labor costs jump 30 percent, I have to close "
            "two locations or dramatically raise prices. It is not politics — it is arithmetic.'\n\n"
            "Academic research remains divided. A 2023 study from the University of Chicago found "
            "that prior state-level minimum wage increases above 15 percent led to measurable "
            "reductions in entry-level employment. A Congressional Budget Office analysis of a "
            "comparable $15 federal proposal projected the elimination of 1.4 million jobs — a "
            "net outcome many economists described as deeply problematic.\n\n"
            "Markets responded cautiously, with restaurant chain stocks slipping 2.1 percent and "
            "retail indices declining in afternoon trading. Congressional moderates have signalled "
            "unease about the timeline, suggesting amendments may be necessary before any floor vote."
        ),
    },
    {
        "source": "The Guardian",
        "text": (
            "Raising the Minimum Wage Is Long Overdue — Workers Cannot Wait\n\n"
            "For millions of Americans working full-time and still unable to afford rent, medicine, "
            "or a single unexpected car repair, last week's minimum wage proposal represents "
            "something painfully simple: the chance to survive with dignity.\n\n"
            "Senate Democrats unveiled legislation that would gradually raise the federal minimum "
            "wage from its current $7.25 per hour — a figure disgracefully unchanged since 2009 "
            "and worth less in real terms than at almost any point in the past fifty years — to "
            "$17 per hour by 2026. For advocates and struggling families, the proposal is both a "
            "moral imperative and a long-delayed act of basic justice.\n\n"
            "'I work fifty hours a week and I still cannot pay my bills,' said Maria Gutierrez, "
            "a 34-year-old hotel housekeeper from Phoenix who earns $10 an hour. 'My kids go to "
            "school in worn shoes because I cannot afford new ones. Nobody who works this hard "
            "should live in poverty in the wealthiest country on Earth.'\n\n"
            "The Economic Policy Institute estimates the raise would lift nearly four million people "
            "out of poverty and benefit over 33 million workers — disproportionately women, Black "
            "and Latino workers, and those without college degrees. It would be the first meaningful "
            "increase in the federal floor wage in more than fifteen years.\n\n"
            "Opponents, largely acting on behalf of corporate interests, once again cry wolf over "
            "job losses — the exact same catastrophic predictions they made in the 1990s and again "
            "in 2007, predictions that never materialised. Evidence from California, Washington, "
            "and New York, all of which enacted higher minimums, shows thriving local economies and "
            "workers doing better, not worse.\n\n"
            "'No one who works full time should live in poverty,' said Senator Priya Rajan, a lead "
            "sponsor. 'This is about dignity. This is about respect for human labor.'\n\n"
            "The time for corporate appeasement has passed. Congress must act — and act now — for "
            "the millions of workers this economy has left behind."
        ),
    },
    {
        "source": "Reuters",
        "text": (
            "Senate Democrats Introduce Bill to Raise Federal Minimum Wage to $17 by 2026\n\n"
            "WASHINGTON, May 5 (Reuters) — Senate Democrats on Thursday introduced legislation "
            "to raise the federal minimum wage from $7.25 per hour to $17 per hour by 2026, "
            "reigniting a congressional debate that has stalled repeatedly over the past decade.\n\n"
            "The bill would increase the minimum wage in three stages: to $13 per hour in 2024, "
            "$15 per hour in 2025, and $17 per hour in 2026. The current federal minimum of $7.25 "
            "has not been raised since 2009, the longest period without an increase since the "
            "federal wage floor was established in 1938.\n\n"
            "The Congressional Budget Office estimated in a prior analysis of a comparable proposal "
            "that raising the federal minimum to $15 would lift 900,000 people out of poverty while "
            "reducing employment by approximately 1.4 million workers. CBO noted that effects would "
            "vary significantly by region and industry.\n\n"
            "Supporters of the legislation, including the Economic Policy Institute, said a $17 "
            "floor would benefit more than 33 million workers and reduce poverty rates, particularly "
            "among women and minority workers. Opponents, including the National Federation of "
            "Independent Business, said the pace of the increase would be too rapid for small "
            "businesses in lower-wage states to absorb.\n\n"
            "Twenty-nine states and Washington D.C. already have minimum wages above the federal "
            "floor. In states such as California and Washington, the minimum wage currently stands "
            "at $16 or higher. In Mississippi, Georgia, and several other Southern states, the "
            "federal minimum remains the controlling rate.\n\n"
            "The legislation faces an uncertain path in the Senate, where it would need 60 votes "
            "to overcome a procedural hurdle. Several moderate Democrats have not yet indicated "
            "their position on the bill. The White House expressed support for raising the minimum "
            "wage but did not endorse the specific timeline in Thursday's legislation.\n\n"
            "The bill was referred to the Senate Health, Education, Labor and Pensions Committee "
            "for review."
        ),
    },
]
