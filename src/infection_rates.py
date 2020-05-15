import math
import numpy as np
import pandas as pd

from datetime import datetime

import matplotlib.pyplot as plt
from scipy.integrate import odeint
import statsmodels.api as sm

from matplotlib.ticker import MultipleLocator, FormatStrFormatter

plt.style.use('ggplot')
font_size = 16
plt.rcParams.update({'font.size': font_size})

# CDC guideline threshold of 10 reported infections per 100k pop every 14 days
reopen_thresh = 10./100000/14

class StateInfections():
    
    def __init__(self):
        pass


    

def plot_infection_trends(state_list, metric = 'infection'):
    num_days_smooth = 7
    metric_dict = {'infection' : ['positive_daily_incr', 'Infections', 'Infection Counts', 'infection_counts'],
                   'hospitalized' : ['hospitalized_daily_incr', 'Hospitializations', 'Hospitializations', 'hospitializations'],
                   'death' : ['death_daily_incr', 'Deaths', 'Deaths', 'deaths']}
    
    # Setting up Subplot layout
    plt_row = np.maximum(len(state_list) // 2, 1)
    if len(state_list) > 1:
        plt_col = 2
    else:
        plt_col = 1
    fig_sz_row = 2 + 3 * plt_row
    fig, axes = plt.subplots(plt_row,plt_col,figsize = (15,fig_sz_row), sharex=True, sharey=True)
    
    for ax, state in zip(axes.flat, state_list):
        # Setting up rolling avg and reopen threshold data
        state_pop = df_usa_pop.loc[df_usa_pop['ABBR'] == state,['POPEST18PLUS2019']].iloc[0,0] 
        state_reopen_thresh = math.ceil(state_pop * reopen_thresh) 
        df2 = df_usa[df_usa['state_id']==state]
        df2['Rolling-{num_days_smooth}mean'] = df2[metric_dict[metric][0]].rolling(window=num_days_smooth, center = True).mean()
        # Data plotted
        ax.bar(df2.d_o_y, df2[metric_dict[metric][0]], label = f"{state}")
        plt.plot(df2.d_o_y, df2['Rolling-{num_days_smooth}mean'], label = f"{state}: {num_days_smooth}-Day Smooth", color='blue')
        ax.axhline(state_reopen_thresh, color = 'black', ls="--", label = f"Reopen Threshold = {state_reopen_thresh}")
        # Major & minor ticks
        ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(direction='out', length=10)
        # Axis Labels
        ax.set_xlabel('Day of Year (2020)') 
        ax.set_ylabel(f'Reported {metric_dict[metric][1]}') 
        ax.label_outer()
        # Coerce Legend to dsplay in desired order
        handles, labels = plt.gca().get_legend_handles_labels()
        order = [2,0,1]
        ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order], 
                  fontsize=12, loc='upper left')
    plt.suptitle(f'{metric_dict[metric][2]} By Day of Year, By State', fontsize=16, y = 0.95)
    plt.show();
    states_str = "-".join(state_list)
    fig.savefig(f"../images/{metric_dict[metric][3]}_by_doy_smoothed_thresh-{states_str}.png", dpi=250)

def dummy_def():
    states = ['NY']
    num_days = 7
    df2 = df_usa[df_usa['state_id'].isin(states)]
    df2['Rolling-{num_days}mean'] = df2['positive_daily_incr'].rolling(window=num_days, center = True).mean()
    fig, ax = plt.subplots(figsize = (12,6))
    for state in states:
        plt.bar(df2.d_o_y, df2['positive_daily_incr'], label = f"{state}: Daily Infections")
        plt.plot(df2.d_o_y, df2['Rolling-{num_days}mean'], label = f"{state}: {num_days}-Day Smooth", color='blue')
        
        ax.axhline(state_reopen_thresh[0], color = 'black', ls="--", label = f"Reopen Threshold = {state_reopen_thresh[0]}")
    
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
    # For the minor ticks, use no labels; default NullFormatter.
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.tick_params(direction='out', length=10)
    ax.set_xlabel('Day of Year (2020)')
    ax.set_ylabel('Infection Count')
    plt.title(f'Daily COVID-19 Infections in {state} (2020)')
    handles, labels = plt.gca().get_legend_handles_labels()
    order = [2,0,1]
    plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order], fontsize=12,loc='upper left')
    plt.show();

def open_merge_files(infection_file_path, df_population):
    df_usa_rates = pd.read_csv(infection_file_path)
    df_usa_rates['datetime'] = pd.to_datetime(df_usa_rates['date'].astype(str), format='%Y%m%d')
    df_usa_rates['d_o_y'] = pd.DatetimeIndex(df_usa_rates['datetime']).dayofyear
    
    df_usa = pd.merge(df_usa_rates, df_population, how='outer', left_on='state', right_on='ABBR',
         left_index=False, right_index=False, sort=True,
         suffixes=('_x', '_y'), copy=True, indicator=False,
         validate=None)[['datetime','d_o_y','NAME', 'state', 'POPESTIMATE2019','positiveIncrease', 
                         'positive', 'negativeIncrease', 'negative', 'pending', 'deathIncrease', 'death', 'recovered', 
                         'hospitalizedIncrease','hospitalized','totalTestResultsIncrease',
                         'totalTestResults','posNeg','total']]
    df_usa.columns = ['datetime','d_o_y','state_name', 'state_id', 'state_pop_2019','positive_daily_incr', 
                  'positive_cum', 'negative_daily_incr', 'negative_cum', 'pending_daily','death_daily_incr', 
                  'death_cum', 'recovered_cum', 'hospitalized_daily_incr','hospitalized_cum',
                  'total_test_results_daily_incr','total_test_results_cum','test_pos_neg_cum','total_tests_cum']
    return df_usa


if __name__ == "__main__":
    df_usa_pop = pd.read_csv('../data/us_state_population_2019.csv')
    df_usa = open_merge_files('../data/us_states_covid19_daily.csv', df_usa_pop)
    
    plot_infection_trends(['NY'], metric = 'infection')
