# Data sources and definitions

This project uses public aggregate road safety data. It does not contain personal information or individual crash records.

## RoadSafetyBC datasets

### Motor Vehicle Fatalities by Road User Type
Public CSV from the Government of British Columbia data catalogue.

Definition: a fatality is a road user who dies within 30 days after injuries from a motor vehicle collision on a public highway, subject to the exclusions documented by RoadSafetyBC.

### Motor Vehicle Fatalities by Region
Annual fatalities by police traffic region.

### Motor Vehicle Serious Injuries by Region
Annual serious injuries by police traffic region. The source describes these as police-attended crashes where an officer assesses that a victim requires more than 24 hours of hospitalization.

### Motor Vehicle Fatalities with Speeding Involvement
Annual fatalities where speeding is identified as involved.

## Refresh cadence

The source catalogue identifies these datasets as annual. The pipeline downloads them during the GitHub Pages build so a redeployment can pick up updated source files.

## Reporting caveats

Police-attended crash data does not represent every collision. Reporting practices have changed over time, so long historical comparisons need context. Aggregate regional data is useful for monitoring and comparison but does not represent precise crash locations.

## Map

The map uses approximate anchor points for four broad police traffic regions. Circle size represents aggregate outcomes. These coordinates are visualization anchors only and must not be interpreted as collision coordinates.

## Forecast

The three-year forecast is a simple linear regression fitted to the latest 10 annual observations. It is included to demonstrate transparent baseline forecasting. It is not a policy forecast, causal model, or official projection.
