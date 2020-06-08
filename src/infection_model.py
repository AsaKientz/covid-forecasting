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
    plt.show()
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
    S, E, I, _ = y

    dSdt = -beta(t) * S * I / N
    dEdt = beta(t) * S * I / N - delta * E
    dIdt = delta * E - gamma * I
    dRdt = gamma * I
    
    return dSdt, dEdt, dIdt, dRdt

def logistic_R_0(t, R_0_start, k, x0, R_0_end):
    '''
    Models the expected change in R_0 (R-naught) from a behavior change event (e.g., lockdown or opening up)
        as a logistic change from one value to a subsequent one, rather than as a single step change.
    
    INPUT:
        - t: the time at which the rates will be calculated
        - R_0_start: R0 before the behavior change event
        - k: parameter to control the rate at which the transition from R_0_start to R_0_end occurs.
        - x0: 'change inflection date' - the center point in the transition from R_0_start to R_0_end. 
        - R_0_end: R0 before the behavior change event
    OUTPUT: 
        - a time based series of R_0 values showing a single transition from R_0_start to R_0_end.
    '''
    return (R_0_start - R_0_end) / (1 + np.exp(-k*(-t+x0))) + R_0_end

def Model(days, N, R_0_start, k, x0, R_0_end):
    '''
    Creates the SEIR model
    
    INPUT:
        - days:
        - N:
        - R_0_start: R0 before the behavior change event
        - k: parameter to control the rate at which the transition from R_0_start to R_0_end occurs.
        - x0: 'change inflection date' - the center point in the transition from R_0_start to R_0_end. 
        - R_0_end: R0 before the behavior change event
    OUTPUT: 
        - t: the time at which the rates will be calculated
        - S: time series of Susceptible people
        - E: time series of Exposed people
        - I: time series of Infected people
        - R: time series of Recovered people
        - R_0_t: a time based series of R_0 values showing a single transition from R_0_start to R_0_end.
    '''
    
    def beta(t):
        '''
        Derives the expected change in beta across a behavior change event, 
            given the change in R_0_t, where beta = R_0_t * gamma

        INPUT:
            - t: the time at which the rates will be calculated
        OUTPUT: 
            - beta_t: a time based series of beta values showing a single transition from
                R_0_start to R_0_end
        '''
        return logistic_R_0(t, R_0_start, k, x0, R_0_end) * gamma
    
    # Initial conditions vector
    S0, E0, I0, R0 = N-1, 1, 0, 0
    y0 = S0, E0, I0, R0
    t = np.linspace(0,days-1,days)
    
    # Integrate the SIR equations over the time grid, t.
    ret = odeint(deriv_seir, y0, t, args=(N, beta, gamma, delta))
    S, E, I, R = ret.T
    R_0_t = [beta(i)/gamma for i in range(len(t))]
    return t, S, E, I, R, R_0_t

def plot_generic(t, S, E, I, R, R_0, x_ticks=None):
    # general SEIR curves
    f, ax = plt.subplots(1,1,figsize=(20,4))
    if x_ticks is None:
        ax.plot(t, S, 'b', alpha=0.7, linewidth=2, label='Susceptible')
        ax.plot(t, E, 'y', alpha=0.7, linewidth=2, label='Exposed')
        ax.plot(t, I, 'r', alpha=0.7, linewidth=2, label='Infected')
        ax.plot(t, R, 'g', alpha=0.7, linewidth=2, label='Recovered')
    else:
        ax.plot(x_ticks, S, 'b', alpha=0.7, linewidth=2, label='Susceptible')
        ax.plot(x_ticks, E, 'y', alpha=0.7, linewidth=2, label='Exposed')
        ax.plot(x_ticks, I, 'r', alpha=0.7, linewidth=2, label='Infected')
        ax.plot(x_ticks, R, 'g', alpha=0.7, linewidth=2, label='Recovered')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        f.autofmt_xdate()
        
    ax.title.set_text('extended SEIR-Model')

    ax.grid(b=True, which='major', c='w', lw=2, ls='-')
    legend = ax.legend()
    legend.get_frame().set_alpha(0.5)
    for spine in ('top', 'right', 'bottom', 'left'):
        ax.spines[spine].set_visible(False)
    plt.show();
    
    # Plot R_0_t
    f = plt.figure(figsize=(20,4))
    ax1 = f.add_subplot(131)
    if x_ticks is None:
        ax1.plot(t, R_0, 'b--', alpha=0.7, linewidth=2, label='R_0')
    else:
        ax1.plot(x_ticks, R_0, 'b--', alpha=0.7, linewidth=2, label='R_0')
        ax1.xaxis.set_major_locator(mdates.YearLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_minor_locator(mdates.MonthLocator())
        f.autofmt_xdate()

    ax1.title.set_text('R_0 over time')
    ax1.grid(b=True, which='major', c='w', lw=2, ls='-')
    legend = ax1.legend()
    legend.get_frame().set_alpha(0.5)
    for spine in ('top', 'right', 'bottom', 'left'):
        ax.spines[spine].set_visible(False)
    plt.show();

def lmfit(params_init_min_max, outbreak_shift = 0):
    R_0_start, k, x0, R_0_end = params_init_min_max
    infect_data = df_cases_region[f'daily_cases_roll{num_days_smooth}mean'][0:40]
    infect_data.fillna(value=0, inplace=True)
    days = outbreak_shift + len(infect_data)
    if outbreak_shift >= 0:
        y_data = np.concatenate((np.zeros(outbreak_shift), infect_data))
    else:
        y_data = y_data[-outbreak_shift:]
    x_data = np.linspace(0, days - 1, days, dtype=int)
    
    def fitter(x, R_0_start, k, x0, R_0_end):
        ret = Model(days, N, R_0_start, k, x0, R_0_end)
        return ret[3][x]
    
    mod = lmfit.Model(fitter)
    for kwarg, (init, mini, maxi) in params_init_min_max.items():
        mod.set_param_hint(str(kwarg), value=init, min=mini, max=maxi, vary=True)
    params = mod.make_params()
    fit_method = "leastsq"
    result = mod.fit(y_data, params, method="least_squares", x=x_data)
    result.plot_fit(datafmt="-");
    return result.best_values


if __name__ == "__main__":
    # CDC guideline threshold of 10 reported infections per 100k pop every 14 days
    reopen_thresh = 10./100000/14
    region_init = ('Colorado','')
    num_days_smooth = 7

    df2, states_pop, date_range = get_state_or_county_data(region_init, num_days_smooth)
    state_reopen_thresh = math.ceil(states_pop * reopen_thresh)

    plot_region_infections(df2, states_pop, date_range, region_init, 
                           num_days_smooth = num_days_smooth, save_fig = True)
    
    # Plots Generic SEIR curves and R0 transition
    plot_generic(*Model(days=100, N=1000, R_0_start=4.0, k=0.5, x0=60, R_0_end=0.80))

    # parameters to fit; form: {parameter: (initial guess, minimum value, max value)}
    params_init_min_max = {"R_0_start": (3.0, 2.0, 20.0), 
                        "k": (2.5, 0.01, 5.0), 
                        "x0": (20, 0, 120), 
                        "R_0_end": (0.9, 0.3, 8.0)}
    N = 1000
    beta = 1.0 # infected person infects 1 other person per day
    D = 4.0 # infections last 4 days
    gamma = 1.0 / D
    delta = 1.0 / 3 # incubation period of 3 days