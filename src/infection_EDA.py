import math
import numpy as np
import pandas as pd

from datetime import datetime

import matplotlib.pyplot as plt
from scipy.integrate import odeint
import statsmodels.api as sm

from matplotlib.ticker import MultipleLocator, FormatStrFormatter

plt.style.use('ggplot')
plt.rcParams.update({'font.size': 12})

from infection_rates import open_merge_files

def plot_state_infections(state_list):
    plt_rw = len(state_list) // 2
    if len(state_list) > 1:
        plt_cl = 2
    else:
        plt_cl = 1
    fig_sz_rw = 2 + 3 * plt_rw
    fig, axes = plt.subplots(plt_rw,plt_cl,figsize = (15,fig_sz_rw), sharex=True, sharey=True)
    for ax, state in zip(axes.flat, state_list):
        df2 = df_usa[df_usa['state_id']==state]
        ax.bar(df2.d_o_y, df2['positive_daily_incr'], label = f"{state}")
        ax.legend(loc='upper left')
        ax.set_xlabel('Day of Year (2020)') 
        ax.set_ylabel('Reported Infections') 
        ax.label_outer()
    plt.suptitle('Infection Counts By Day of Year, By State', fontsize=16, y = 0.95)
    plt.show();
    states_str = "-".join(state_list)
    fig.savefig(f"../images/infection_counts_by_doy-{states_str}.png", dpi=250)

def plot_state_deaths(state_list):
    plt_rw = len(state_list) // 2
    if len(state_list) > 1:
        plt_cl = 2
    else:
        plt_cl = 1
    fig_sz_rw = 2 + 3 * plt_rw
    fig, axes = plt.subplots(plt_rw,plt_cl,figsize = (15,fig_sz_rw), sharex=True, sharey=True)
    for ax, state in zip(axes.flat, state_list):
        df2 = df_usa[df_usa['state_id']==state]
        ax.bar(df2.d_o_y, df2['death_daily_incr'], label = f"{state}")
        ax.legend(loc='upper left')
        ax.set_xlabel('Day of Year (2020)') 
        ax.set_ylabel('Reported Deaths') 
        ax.label_outer()
    plt.suptitle('Deaths By Day of Year, By State', fontsize=16, y = 0.95)
    plt.show();
    states_str = "-".join(state_list)
    fig.savefig(f"../images/deaths_by_doy-{states_str}.png", dpi=250)


if __name__ == "__main__":
    df_usa_pop = pd.read_csv('../data/us_state_population_2019.csv')
    df_usa = open_merge_files('../data/us_states_covid19_daily.csv', df_usa_pop)
    
    plot_state_infections(['NY', 'NJ'])
    plot_state_infections(['CO', 'FL', 'CA', 'MO'])
    plot_state_deaths(['NY', 'NJ'])
