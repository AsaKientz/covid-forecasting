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

def plot_state_daily_data(state_list, metric = 'infection'):
    metric_dict = {'infection' : ['positive_daily_incr', 'Infections', 'Infection Counts', 'infection_counts'],
                   'hospitalized' : ['hospitalized_daily_incr', 'Hospitializations', 'Hospitializations', 'hospitializations'],
                   'death' : ['death_daily_incr', 'Deaths', 'Deaths', 'deaths']}
    plt_row = np.maximum(len(state_list) // 2, 1)
    if len(state_list) > 1:
        plt_cl = 2
    else:
        plt_cl = 1
    fig_sz_rw = 2 + 3 * plt_rw
    fig, axes = plt.subplots(plt_rw,plt_cl,figsize = (15,fig_sz_rw), sharex=True, sharey=True)
    for ax, state in zip(axes.flat, state_list):
        df2 = df_usa[df_usa['state_id']==state]
        ax.bar(df2.d_o_y, df2[metric_dict[metric][0]], label = f"{state}")
        ax.legend(loc='upper left')
        ax.set_xlabel('Day of Year (2020)') 
        ax.set_ylabel(f'Reported {metric_dict[metric][1]}') 
        ax.label_outer()
    plt.suptitle(f'{metric_dict[metric][2]} By Day of Year, By State', fontsize=16, y = 0.95)
    plt.show();
    states_str = "-".join(state_list)
    fig.savefig(f"../images/{metric_dict[metric][3]}_by_doy-{states_str}.png", dpi=250)


if __name__ == "__main__":
    df_usa_pop = pd.read_csv('../data/us_state_population_2019.csv')
    df_usa = open_merge_files('../data/us_states_covid19_daily.csv', df_usa_pop)
    
    plot_state_daily_data(['NY', 'NJ'], metric = 'infection')
    plot_state_daily_data(['CO', 'FL', 'CA', 'MO'], metric = 'infection')
    plot_state_daily_data(['NY', 'NJ'], metric = 'death')
