
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

# CHART 5: small multiples by channel
fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=True)
channels = ['paid_search','organic','email','referral']
for ax, c in zip(axes, channels):
    sub = df[df.channel==c]
    p = sub.groupby(['month','user_type']).agg(v=('visits','sum'), cc=('conversions','sum')).reset_index()
    p['v2c'] = p.cc/p.v
    pp = p.pivot(index='month', columns='user_type', values='v2c')
    ax.plot(range(6), pp['new'].values*100, color=BLUE, lw=2, marker='o', ms=5)
    ax.plot(range(6), pp['returning'].values*100, color=ORANGE, lw=2, marker='o', ms=5)
    ax.set_xticks([0, 5]); ax.set_xticklabels(['Jan','Jun'])
    ax.set_title(c.replace('_',' '), fontsize=11, pad=6)
    ax.set_ylim(3, 17)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.0f}%'.format(x)))
    ax.annotate('{:.1f}%'.format(pp['new'].iloc[-1]*100), (5, pp['new'].iloc[-1]*100),
                xytext=(3, 0), textcoords='offset points', fontsize=9, color=BLUE)
    ax.annotate('{:.1f}%'.format(pp['returning'].iloc[-1]*100), (5, pp['returning'].iloc[-1]*100),
                xytext=(3, 0), textcoords='offset points', fontsize=9, color=ORANGE)
axes[0].set_ylabel('Visit-to-conversion rate')
axes[0].text(2.5, 4.5, 'new', color=BLUE, fontsize=10, weight='bold')
axes[0].text(2.5, 15.5, 'returning', color=ORANGE, fontsize=10, weight='bold')
fig.suptitle('Every channel shows the same split: new users up, returning users down',
             fontsize=13, weight='bold', x=0.02, ha='left', y=1.02)
plt.tight_layout()
fig.savefig(CHARTS + '/05_channel_small_multiples.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('saved 05_channel_small_multiples.png')

# CHART 6: funnel step location
ut = df.groupby(['month','user_type']).agg(v=('visits','sum'),s=('signups','sum'),cc=('conversions','sum')).reset_index()
ut['v2s'] = ut.s/ut.v
ut['s2c'] = ut.cc/ut.s

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
# Panel A: v2s (story step)
ax = axes[0]
for u, col in [('new', BLUE), ('returning', ORANGE)]:
    sub = ut[ut.user_type==u].sort_values('month')
    ax.plot(range(6), sub.v2s.values*100, color=col, lw=2.5, marker='o', ms=6)
    ax.annotate('{:.1f}% -> {:.1f}%\n({:+.1f}pp)'.format(sub.v2s.iloc[0]*100, sub.v2s.iloc[-1]*100,
                                                         (sub.v2s.iloc[-1]-sub.v2s.iloc[0])*100),
                (5, sub.v2s.iloc[-1]*100), xytext=(8, 0), textcoords='offset points',
                fontsize=9.5, color=col, weight='bold', va='center')
ax.set_xticks(range(6)); ax.set_xticklabels(month_labels)
ax.set_ylim(5, 32)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.0f}%'.format(x)))
ax.set_title('Visit -> signup (where the movement lives)', fontsize=12)
ax.set_ylabel('Rate')
ax.text(2.5, 11, 'new', color=BLUE, fontsize=10, weight='bold')
ax.text(2.5, 23, 'returning', color=ORANGE, fontsize=10, weight='bold')

# Panel B: s2c (stable step, grayed)
ax = axes[1]
for u, col in [('new', GRAY), ('returning', GRAY)]:
    sub = ut[ut.user_type==u].sort_values('month')
    ax.plot(range(6), sub.s2c.values*100, color=GRAY, lw=2.5, marker='o', ms=6)
    ax.annotate('{:.1f}% -> {:.1f}%'.format(sub.s2c.iloc[0]*100, sub.s2c.iloc[-1]*100),
                (5, sub.s2c.iloc[-1]*100), xytext=(8, 0), textcoords='offset points',
                fontsize=9.5, color=DARKGR, weight='bold', va='center')
ax.set_xticks(range(6)); ax.set_xticklabels(month_labels)
ax.set_ylim(45, 67)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:.0f}%'.format(x)))
ax.set_title('Signup -> conversion (stable; product is fine)', fontsize=12)
ax.text(2.5, 62, 'new', color=DARKGR, fontsize=10, weight='bold')
ax.text(2.5, 47, 'returning', color=DARKGR, fontsize=10, weight='bold')

fig.suptitle('The movement is at visit -> signup, not post-signup -- this is an acquisition/targeting problem, not a product one',
             fontsize=12.5, weight='bold', x=0.02, ha='left', y=1.02)
plt.tight_layout()
fig.savefig(CHARTS + '/06_funnel_step_location.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('saved 06_funnel_step_location.png')

# CHART 7: opportunity sizing
jun_new_v = df[(df.month=='2026-06-01')&(df.user_type=='new')].visits.sum()
jun_ret_v = df[(df.month=='2026-06-01')&(df.user_type=='returning')].visits.sum()
jan_new_v = df[(df.month=='2026-01-01')&(df.user_type=='new')].visits.sum()
jun_new_c = df[(df.month=='2026-06-01')&(df.user_type=='new')].conversions.sum()
jun_ret_c = df[(df.month=='2026-06-01')&(df.user_type=='returning')].conversions.sum()
jan_new_rate = df[(df.month=='2026-01-01')&(df.user_type=='new')].conversions.sum() / jan_new_v
jan_ret_rate = df[(df.month=='2026-01-01')&(df.user_type=='returning')].conversions.sum() / df[(df.month=='2026-01-01')&(df.user_type=='returning')].visits.sum()
jun_new_rate = jun_new_c / jun_new_v
jun_ret_rate = jun_ret_c / jun_ret_v

ret_missed = (jan_ret_rate - jun_ret_rate) * jun_ret_v
new_missed = (jan_new_v - jun_new_v) * jun_new_rate
actual = jun_new_c + jun_ret_c

fig, ax = plt.subplots(figsize=(10.5, 4.8))
ax.bar(0, actual, color=DARKGR, width=0.55)
ax.text(0, actual + 80, '{:,.0f}'.format(actual), ha='center', fontsize=11, weight='bold')

ax.bar(1, actual, color=DARKGR, width=0.55)
ax.bar(1, ret_missed, bottom=actual, color=ORANGE, width=0.55, alpha=0.85)
ax.text(1, actual + ret_missed + 80, '{:,.0f}'.format(actual+ret_missed), ha='center', fontsize=11, weight='bold')
ax.text(1, actual + ret_missed/2, '+{:,.0f}\nreturning rate'.format(ret_missed), ha='center', fontsize=10, color='white', weight='bold')

ax.bar(2, actual, color=DARKGR, width=0.55)
ax.bar(2, ret_missed, bottom=actual, color=ORANGE, width=0.55, alpha=0.85)
ax.bar(2, new_missed, bottom=actual+ret_missed, color=BLUE, width=0.55, alpha=0.9)
ax.text(2, actual + ret_missed + new_missed + 80, '{:,.0f}'.format(actual+ret_missed+new_missed), ha='center', fontsize=11, weight='bold')
ax.text(2, actual + ret_missed + new_missed/2, '+{:,.0f}\nnew volume'.format(new_missed), ha='center', fontsize=10, color='white', weight='bold')
ax.text(2, actual/2, '{:,.0f}\nbase'.format(actual), ha='center', fontsize=10, color='white', weight='bold')

ax.set_xticks([0, 1, 2])
ax.set_xticklabels([
    'Actual Jun\nconversions',
    'Recover returning\nrate to Jan (13.8%)',
    'Recover new-user\nvolume to Jan (~33k visits)',
], fontsize=10)
ax.set_ylim(0, 7000)
ax.set_ylabel('Monthly conversions')
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: '{:,.0f}'.format(x)))
ax.set_title('Fixing both would add ~{:,.0f} monthly conversions (+{:.0f}% vs June)'.format(ret_missed + new_missed, (ret_missed+new_missed)/actual*100), fontsize=13)
ax.text(0.02, 0.94,
        'Returning-rate recovery: ~{:,.0f}/mo (~{:,.0f}/yr).  New-user volume recovery at current rate: ~{:,.0f}/mo.'.format(ret_missed, ret_missed*12, new_missed),
        transform=ax.transAxes, fontsize=10, color='#6B7280', style='italic', va='top')
plt.tight_layout()
fig.savefig(CHARTS + '/07_opportunity_sizing.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('saved 07_opportunity_sizing.png  ret_missed={:.0f} new_missed={:.0f}'.format(ret_missed, new_missed))
