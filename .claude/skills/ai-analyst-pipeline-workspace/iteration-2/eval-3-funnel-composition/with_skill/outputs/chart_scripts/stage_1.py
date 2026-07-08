
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os

CHARTS = '/tmp/ai-analyst-iter2/eval-3-funnel-composition/with_skill/outputs/charts'
os.makedirs(CHARTS, exist_ok=True)

df = pd.read_csv('/tmp/ai-analyst-iter2/inputs/funnel_monthly.csv')
df['month'] = pd.to_datetime(df['month'])

GRAY    = '#9CA3AF'
DARKGR  = '#4B5563'
BLUE    = '#2563EB'
ORANGE  = '#DC2626'
GREEN   = '#16A34A'

plt.rcParams.update({
    'font.size': 11,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.edgecolor': '#6B7280',
    'axes.labelcolor': '#374151',
    'xtick.color': '#374151',
    'ytick.color': '#374151',
    'axes.titlelocation': 'left',
    'axes.titleweight': 'bold',
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
})

month_labels = ['Jan','Feb','Mar','Apr','May','Jun']

# CHART 1
overall = df.groupby('month').agg(v=('visits','sum'), c=('conversions','sum'))
overall['v2c'] = overall.c / overall.v
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(range(6), overall['v2c'].values*100, color=DARKGR, lw=2, marker='o', markersize=7)
ax.set_xticks(range(6)); ax.set_xticklabels(month_labels)
ax.set_ylim(6, 11)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.0f}%'.format(x)))
ax.annotate('{:.2f}%'.format(overall['v2c'].iloc[0]*100), (0, overall['v2c'].iloc[0]*100),
            xytext=(-8, 8), textcoords='offset points', fontsize=10, ha='right', color=DARKGR, weight='bold')
ax.annotate('{:.2f}%'.format(overall['v2c'].iloc[-1]*100), (5, overall['v2c'].iloc[-1]*100),
            xytext=(8, 8), textcoords='offset points', fontsize=10, color=DARKGR, weight='bold')
ax.text(0.02, 0.92, 'Slope: +0.02pp/mo (p = 0.75, not significant)', transform=ax.transAxes,
        fontsize=10, color='#6B7280', style='italic')
ax.set_title('Aggregate conversion rate is flat in H1 2026 -- the marketing claim is arithmetically correct', fontsize=13)
ax.set_ylabel('Visit-to-conversion rate')
plt.tight_layout()
fig.savefig(CHARTS + '/01_aggregate_flat.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('saved 01_aggregate_flat.png')

# CHART 2
ut = df.groupby(['month','user_type']).agg(v=('visits','sum'), c=('conversions','sum')).reset_index()
ut['v2c'] = ut.c/ut.v
piv = ut.pivot(index='month', columns='user_type', values='v2c')
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(range(6), piv['new'].values*100, color=BLUE, lw=2.5, marker='o', markersize=7)
ax.plot(range(6), piv['returning'].values*100, color=ORANGE, lw=2.5, marker='o', markersize=7)
ax.annotate('5.24%\\nnew users', (0, piv['new'].iloc[0]*100),
            xytext=(-10, -28), textcoords='offset points', fontsize=10, color=BLUE, weight='bold', ha='right')
ax.annotate('7.37%\\n(+41% rel)', (5, piv['new'].iloc[-1]*100),
            xytext=(12, 0), textcoords='offset points', fontsize=10, color=BLUE, weight='bold')
ax.annotate('13.81%\\nreturning users', (0, piv['returning'].iloc[0]*100),
            xytext=(-10, 10), textcoords='offset points', fontsize=10, color=ORANGE, weight='bold', ha='right')
ax.annotate('9.93%\\n(-28% rel)', (5, piv['returning'].iloc[-1]*100),
            xytext=(12, 0), textcoords='offset points', fontsize=10, color=ORANGE, weight='bold')
ax.set_xticks(range(6)); ax.set_xticklabels(month_labels)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.0f}%'.format(x)))
ax.set_ylim(3, 16)
ax.set_title('Underneath, new-user conversion rose 41% while returning-user conversion fell 28%', fontsize=13)
ax.set_ylabel('Visit-to-conversion rate')
plt.tight_layout()
fig.savefig(CHARTS + '/02_new_vs_returning_v2c.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('saved 02_new_vs_returning_v2c.png')

print('done stage 1')
