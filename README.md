# Safe to Reopen?  Evidence-based

![alt text](/images/crowd.png) <!-- width="100%">

Galvanize DSI Capstone around forecasting COVID-19 infection rates

---
## Motivation

A

---
## Background



### Incidence Threshold
The CDC defines low incidence as 10 or fewer new cases per 100,000 people over a period of 14 days. This rate is equivalent to 0.71 new cases per 100,000 people per day, or about 2,300 new cases per day in the United States.

---

## Raw Data Description

**Daily US State data file** - includes

`State Name`
`State Abbr`

`Date`

`Day of Year`

``

XXXX

Additionally, population data by state (estimated for end of year 2019) was included from the [US Census](https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/state/detail/SCPRC-EST2019-18+POP-RES.csv) website.

## EDA - Time Series Processing

### Weekly <|trend|>

A 7-day cyclic behavior can be seen in infection rates and deaths for most states (as well as world countries).  Infections and Deaths are lowest on Mondays and Tuesdays; highest on Thursdays and Friday.

It's unclear what drives this trend; i.e., if it's an artifact of patient's behavior with medical care, a lag in reporting data on certain days, etc.  

This periodicity needs to be smoothed.

A 7-day rolling average was applied to the data to smooth out peaks and troughs.

## SIR Model Overview
 - A compartmental model used to model infectious diseases.

![alt text](/images/SIR_Flow_Diagram.png "SIR Model Flow")

![alt text](/images/SIR-equations.png "SIR Equations")

## Assumptions
- A given population is treated as homogenous (i.e., within a state, there are no population density impacts).  There is also a single initial infection point per geographic area.
- Each geographic region is self-contained (i.e., infections only come from existing sources within and not from travel, immigration, etc.)
- Testing is widespread enough to catch nearly all the infections in the population. 
- 
- This SIR model assumes immunity upon recovery - this may be true woth COVID-19, but

## Sample fits


https://www.americanprogress.org/issues/healthcare/news/2020/05/04/484373/evidence-based-thresholds-states-must-meet-control-coronavirus-spread-safely-reopen-economies/



### References and Kudos
- [CDC COVID-19 Forecasts](https://www.cdc.gov/coronavirus/2019-ncov/covid-data/forecasting-us.html)
- [Columbia University Epidemiology](https://columbia.maps.arcgis.com/apps/webappviewer/index.html?id=ade6ba85450c4325a12a5b9c09ba796c)
- []()
- [Center for American Progress - *Thresholds States Must Meet To Control Coronavirus Spread and Safely Reopen*](https://www.americanprogress.org/issues/healthcare/news/2020/05/04/484373/evidence-based-thresholds-states-must-meet-control-coronavirus-spread-safely-reopen-economies/)
- [Wikipedia - *Compartmental models in epidemiology*](https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology)
- Denver DSI Instructional team for all the

