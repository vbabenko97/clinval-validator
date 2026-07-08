
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

month_labels = ['Jan','Feb','Mar','Apr','May','Jun']

# CHART 3: visit mix stacked area
ut_v = df.groupby(['month','user_type']).visits.sum().unstack()
ut_share = ut_v.div(ut_v.sum(axis=1), axis=0)
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.fill_between(range(6), 0, ut_share['new'].values*100, color=BLUE, alpha=0.85)
ax.fill_between(range(6), ut_share['new'].values*100, 100, color=ORANGE, alpha=0.75)
ax.axhline(50, color='white', lw=1, alpha=0.8, linestyle=':')
ax.text(0.15, 30, 'new', color='white', fontsize=14, weight='bold', ha='center')
ax.text(5, 75, 'returning', color='white', fontsize=14, weight='bold', ha='right')
ax.annotate('60%', (0, 60), xytext=(-35, 0), textcoords='offset points', fontsize=10, color=BLUE, weight='bold', ha='right',
            arrowprops=dict(arrowstyle='-', color='#9CA3AF', lw=0.8))
ax.annotate('46%', (5, 46), xytext=(25, 0), textcoords='offset points', fontsize=10, color=BLUE, weight='bold',
            arrowprops=dict(arrowstyle='-', color='#9CA3AF', lw=0.8))
ax.annotate('40%', (0, 80), xytext=(-35, 0), textcoords='offset points', fontsize=10, color=ORANGE, weight='bold', ha='right',
            arrowprops=dict(arrowstyle='-', color='#9CA3AF', lw=0.8))
ax.annotate('54%', (5, 73), xytext=(25, 0), textcoords='offset points', fontsize=10, color=ORANGE, weight='bold',
            arrowprops=dict(arrowstyle='-', color='#9CA3AF', lw=0.8))
ax.set_xticks(range(6)); ax.set_xticklabels(month_labels)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.0f}%'.format(x)))
ax.set_xlim(-0.1, 5.1); ax.set_ylim(0, 100)
ax.set_title('Visit mix flipped: returning-user share climbed from 40% to 54% in six months', fontsize=13)
ax.set_ylabel('Share of monthly visits')
plt.tight_layout()
fig.savefig(CHARTS + '/03_visit_mix_shift.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('saved 03_visit_mix_shift.png')

# CHART 4: waterfall
jan = df[df.month=='2026-01-01']
jun = df[df.month=='2026-06-01']
jan_share = jan.groupby('user_type').visits.sum() / jan.visits.sum()
jun_share = jun.groupby('user_type').visits.sum() / jun.visits.sum()
jan_new_rate = jan[jan.user_type=='new'].conversions.sum() / jan[jan.user_type=='new'].visits.sum()
jan_ret_rate = jan[jan.user_type=='returning'].conversions.sum() / jan[jan.user_type=='returning'].visits.sum()
jun_new_rate = jun[jun.user_type=='new'].conversions.sum() / jun[jun.user_type=='new'].visits.sum()
jun_ret_rate = jun[jun.user_type=='returning'].conversions.sum() / jun[jun.user_type=='returning'].visits.sum()
jan_rate = pd.Series({'new': jan_new_rate, 'returning': jan_ret_rate})
jun_rate = pd.Series({'new': jun_new_rate, 'returning': jun_ret_rate})
jan_agg = (jan_share * jan_rate).sum()
jun_agg = (jun_share * jun_rate).sum()
rate_effect = (jan_share * jun_rate).sum() - jan_agg
mix_effect = jun_agg - jan_agg - rate_effect

labels = ['Jan 2026\nactual', 'Rate shift\n(subgroup rates)', 'Mix shift\n(to more returning)', 'Jun 2026\nactual']
fig, ax = plt.subplots(figsize=(9.5, 5))
# Bars
ax.bar(0, jan_agg*100, color=DARKGR, width=0.55)
ax.text(0, jan_agg*100 + 0.08, '{:.2f}%'.format(jan_agg*100), ha='center', fontsize=11, weight='bold')
bottom = jan_agg*100
h = rate_effect*100
color = GREEN if h >= 0 else ORANGE
ax.bar(1, h, bottom=bottom, color=color, width=0.55)
ax.text(1, bottom + h/2, '{:+.2f}pp'.format(h), ha='center', fontsize=11, weight='bold', color='white')
bottom2 = bottom + h
h2 = mix_effect*100
color2 = GREEN if h2 >= 0 else ORANGE
ax.bar(2, h2, bottom=bottom2, color=color2, width=0.55)
ax.text(2, bottom2 + h2/2, '{:+.2f}pp'.format(h2), ha='center', fontsize=11, weight='bold', color='white')
ax.bar(3, jun_agg*100, color=DARKGR, width=0.55)
ax.text(3, jun_agg*100 + 0.08, '{:.2f}%'.format(jun_agg*100), ha='center', fontsize=11, weight='bold')
for (x1,y1),(x2,y2) in [((0.3, jan_agg*100),(0.7, jan_agg*100)),
                        ((1.3, bottom+h),(1.7, bottom+h)),
                        ((2.3, bottom2+h2),(2.7, bottom2+h2))]:
    ax.plot([x1, x2], [y1, y2], 'k:', lw=0.8, color='#9CA3AF')
ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=10)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.1f}%'.format(x)))
ax.set_ylim(7.6, 10.5)
ax.set_title('Without the mix shift, conversion rate would have risen 1.1pp', fontsize=13)
ax.set_ylabel('Visit-to-conversion rate')
ax.text(0.02, 0.95, 'Rate effect (subgroup rates changed) added +{:.2f}pp;  mix effect (more returning users) subtracted {:.2f}pp;  net +{:.2f}pp.'.format(rate_effect*100, abs(mix_effect)*100, (jun_agg-jan_agg)*100),
        transform=ax.transAxes, fontsize=10, color='#6B7280', style='italic', va='top')
plt.tight_layout()
fig.savefig(CHARTS + '/04_waterfall_decomposition.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('saved 04_waterfall_decomposition.png  rate={:+.3f}pp mix={:+.3f}pp'.format(rate_effect*100, mix_effect*100))

print('done stage 2')
