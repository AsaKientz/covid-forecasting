import math
import numpy as np
import pandas as pd

from datetime import datetime
from datetime import date

import matplotlib.pyplot as plt
from scipy.integrate import odeint
import statsmodels.api as sm

from matplotlib.ticker import MultipleLocator, FormatStrFormatter

import pymc3 as pm
from pymc3.ode import DifferentialEquation
import arviz as az
import theano


import lmfit
from lmfit.lineshapes import gaussian, lorentzian

plt.style.use('ggplot')
font_size = 14
plt.rcParams.update({'font.size': font_size})


# Get data
def get_state_or_county_data(region, num_days = 7):
    '''
    Extracts the daily and cumulative totals of infections and deaths for a given region,
        as well as population for that region.  
    
    INPUT:
        - region: A tuple for the region of interest, of the form ('State':'County').
            The County should not have the term 'County' in it.
            Data for the entire state can be extracted by listing the 'Entire State' for the county.
        - num_days: number of days to apply centered rolling average
    OUTPUT: 
        - df_cases_deaths: A Pandas dataframe with time series of infections 
            and deaths (total and daily) for the specified region
        - region_pop: (Int64) Population (2019 estimate) for the specified region 
    '''
    def get_full_date_range(df):
        df['date'] = pd.to_datetime(df.date, format = "%Y/%m/%d")
        date_range = (pd.Timestamp('2020-03-01'), df['date'].max())
        return date_range
    
    if region[1]=='Entire State' or region[1]=='':
        df_cases = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
        date_range = get_full_date_range(df_cases)
        df_cases_region = df_cases.loc[(df_cases['state']==region[0])].reset_index()
        county_popul = region[0]
    else:
        df_cases = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv')
        date_range = get_full_date_range(df_cases)
        df_cases_region = df_cases.loc[(df_cases['state']==region[0]) & (df_cases['county'].str.startswith(region[1]))].reset_index()
        county_popul = region[1] + ' County'
    
    df_cases_region['daily_cases'] = df_cases_region['cases'] - df_cases_region['cases'].shift(1)
    df_cases_region['daily_cases'].fillna(value=0, inplace=True)
    df_cases_region['daily_deaths'] = df_cases_region['deaths'] - df_cases_region['deaths'].shift(1)
    df_cases_region['daily_deaths'].fillna(value=0, inplace=True)
    df_cases_region[f'daily_cases_roll{num_days}mean'] = df_cases_region['daily_cases'].rolling(window=num_days, center = True).mean()
   
    cols_to_move = ['cases', 'daily_deaths','deaths']
    df_cases_region = df_cases_region[[ col for col in df_cases_region.columns if col not in cols_to_move] + cols_to_move]
    
    df_pop = pd.read_csv('https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/co-est2019-alldata.csv', encoding='latin-1')
    region_pop = df_pop.loc[(df_pop['STNAME']==region[0]) & (df_pop['CTYNAME']==county_popul), 'POPESTIMATE2019'].values[0]
    
    return df_cases_region, region_pop, date_range


def plot_region_infections(df, states_pop, date_range, region_init, num_days_smooth = 7, save_fig = False):
    '''
    Plots the infections of a region over time wiht a smooth fit and a reopen target threshold.
    
    INPUT:
        - df:
        - states_pop:
        - date_range:
        - region_init:
        - num_days_smooth: 
        - save_fig:
    OUTPUT: 
        - Plot of infections over time
        - (Optional) Plot saved as a .png file.
    '''
    fig, ax = plt.subplots(figsize = (12,6))

    if region_init[1] == 'Entire State' or region_init[1] == '':
        label_text = f'{region_init[0]} (Full State)'
    else:
        label_text = f'{region_init[1]} County, {region_init[0]}'
    latest_data_pull = max(df.date).strftime("%y_%m_%d")

    plt.plot(df.date, df[f'daily_cases_roll{num_days_smooth}mean'], 
             label = f"{label_text}: {num_days_smooth}-Day Smooth", color='blue')
    ax.axhline(state_reopen_thresh, color = 'black', ls="--", 
               label = f"Reopen Threshold = {state_reopen_thresh}")
    ax.bar(df.date, df['daily_cases'], label = label_text)
    ax.legend(loc='upper left')
    ax.set_xlabel('Date') 
    ax.set_ylabel('Reported Infections') 
    ax.label_outer()
    plt.xlim(date_range[0], date_range[1])
    plt.xticks(np.arange(date_range[0], max(df.date) + pd.DateOffset(1), 1000000*60*60*24*30))
    plt.suptitle(f'Infection Counts By Date - {label_text}', fontsize=16, y = 0.95)
    plt.show();
    if save_fig:
        fig.savefig(f'../images/daily_infection_rates_target_{label_text.replace(" ", "_")}_{latest_data_pull}.png', dpi=250)

def deriv_seir(y, t, N, beta, gamma, delta):
    '''
    Calculates the net change in population for each compartment of the SEIR model
        at a given time t.
    
    INPUT:
        - y:     a variable packed with the 4 compartments of the SEIR model
        - t:     the time at which the rates will be calculated
        - N:     the total population available; equals the sum of S+E+I+R
        - beta:  the expected amount of people an infected person infects per day
        - gamma: the fraction of infected people recovering per day (= 1 / D, where D is the
            number of days an infected person has and can spread the disease).
        - delta: length of incubation period (how long a person is Exposed before becoming Infected)
    OUTPUT: 
        - dSdt: the net change of Susceptible people for the time, t, given
        - dEdt: the net change of Exposed     people for the time, t, given
        - dIdt: the net change of Infected    people for the time, t, given
        - dRdt: the net change of Recovered   people for the time, t, given
    '''
    S, E, I, R = y

    dSdt = -beta(t) * S * I / N
    dEdt = beta(t) * S * I / N - delta * E
    dIdt = delta * E - gamma * I
    dRdt = gamma * I
    
    return dSdt, dEdt, dIdt, dRdt

if __name__ == "__main__":
    # CDC guideline threshold of 10 reported infections per 100k pop every 14 days
    reopen_thresh = 10./100000/14
    region_init = ('Colorado','')
    num_days_smooth = 7

    df2, states_pop, date_range = get_state_or_county_data(region_init, num_days_smooth)
    state_reopen_thresh = math.ceil(states_pop * reopen_thresh)

    plot_region_infections(df2, states_pop, date_range, region_init, 
                           num_days_smooth = num_days_smooth, save_fig = True)
