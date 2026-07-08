
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os

CHARTS = '/tmp/ai-analyst-iter2/eval-3-funnel-composition/with_skill/outputs/charts'
df = pd.read_csv('/tmp/ai-analyst-iter2/inputs/funnel_monthly.csv')
df['month'] = pd.to_datetime(df['month'])

GRAY='#9CA3AF'; DARKGR='#4B5563'; BLUE='#2563EB'; ORANGE='#DC2626'; GREEN='#16A34A'

plt.rcParams.update({
    'font.size': 11,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.edgecolor': '#6B7280',
    'axes.titlelocation': 'left',
    'axes.titleweight': 'bold',
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
})

# Waterfall using standard additive decomposition
jan = df[df.month=='2026-01-01']
jun = df[df.month=='2026-06-01']
jan_share = jan.groupby('user_type').visits.sum() / jan.visits.sum()
jun_share = jun.groupby('user_type').visits.sum() / jun.visits.sum()
jan_rate = jan.groupby('user_type').apply(lambda g: g.conversions.sum()/g.visits.sum(), include_groups=False)
jun_rate = jun.groupby('user_type').apply(lambda g: g.conversions.sum()/g.visits.sum(), include_groups=False)
agg_jan = (jan_share * jan_rate).sum()
agg_jun = (jun_share * jun_rate).sum()

mix_eff = ((jun_share - jan_share) * jan_rate).sum()      # +1.21pp
rate_eff = (jan_share * (jun_rate - jan_rate)).sum()       # -0.28pp
interact = ((jun_share - jan_share) * (jun_rate - jan_rate)).sum()  # -0.85pp

# Waterfall bars
labels = ['Jan 2026\naggregate', 'Mix effect\n(more returning,\nat Jan rates)', 'Rate effect\n(subgroup rates\nchanged)', 'Interaction\n(both shifted\ntogether)', 'Jun 2026\naggregate']
fig, ax = plt.subplots(figsize=(11, 5.2))
# Bars: start, mix, rate, interact, end
ax.bar(0, agg_jan*100, color=DARKGR, width=0.55)
ax.text(0, agg_jan*100 + 0.08, '{:.2f}%'.format(agg_jan*100), ha='center', fontsize=11, weight='bold')

bottom = agg_jan*100
h = mix_eff*100
color = GREEN if h >= 0 else ORANGE
ax.bar(1, h, bottom=bottom, color=color, width=0.55)
ax.text(1, bottom + h/2, '{:+.2f}pp'.format(h), ha='center', fontsize=11, weight='bold', color='white')

bottom2 = bottom + h
h2 = rate_eff*100
color2 = GREEN if h2 >= 0 else ORANGE
ax.bar(2, h2, bottom=bottom2, color=color2, width=0.55)
ax.text(2, bottom2 + h2/2, '{:+.2f}pp'.format(h2), ha='center', fontsize=11, weight='bold', color='white')

bottom3 = bottom2 + h2
h3 = interact*100
color3 = GREEN if h3 >= 0 else ORANGE
ax.bar(3, h3, bottom=bottom3, color=color3, width=0.55)
ax.text(3, bottom3 + h3/2, '{:+.2f}pp'.format(h3), ha='center', fontsize=11, weight='bold', color='white')

ax.bar(4, agg_jun*100, color=DARKGR, width=0.55)
ax.text(4, agg_jun*100 + 0.08, '{:.2f}%'.format(agg_jun*100), ha='center', fontsize=11, weight='bold')

# Connectors
for (x1,y1),(x2,y2) in [
    ((0.3, agg_jan*100),(0.7, agg_jan*100)),
    ((1.3, bottom+h),(1.7, bottom+h)),
    ((2.3, bottom2+h2),(2.7, bottom2+h2)),
    ((3.3, bottom3+h3),(3.7, bottom3+h3)),
]:
    ax.plot([x1, x2], [y1, y2], linestyle=':', lw=0.8, color='#9CA3AF')

ax.set_xticks(range(5)); ax.set_xticklabels(labels, fontsize=10)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.1f}%'.format(x)))
ax.set_ylim(6.8, 10.8)
ax.set_title('Flat aggregate hides cancelling forces: +1.2pp mix gain undone by -1.1pp from falling returning rate', fontsize=12.5)
ax.set_ylabel('Visit-to-conversion rate')
ax.text(0.02, 0.96,
        'Mix shift toward returning users would have RAISED conversion (if Jan rates held); but returning rates collapsed, so the compounded effect nearly cancels the gain.',
        transform=ax.transAxes, fontsize=9.5, color='#6B7280', style='italic', va='top')
plt.tight_layout()
fig.savefig(CHARTS + '/04_waterfall_decomposition.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('rewrote 04_waterfall_decomposition.png, components: mix={:+.3f} rate={:+.3f} interact={:+.3f} sum={:+.3f}'.format(
    mix_eff*100, rate_eff*100, interact*100, (mix_eff+rate_eff+interact)*100))
