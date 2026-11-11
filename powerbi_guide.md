# Build the same dashboard in Power BI

The CSV in `data/hr_data_sample.csv` can be loaded straight into Power BI Desktop (or Tableau). This guide lists the measures and visuals to recreate the Python dashboard. It was written without access to Power BI, so treat it as a starting point and adjust names if your table is called something other than `HR`.

## 1. Load the data
Home → Get data → Text/CSV → choose `hr_data_sample.csv` → Load. Rename the table to `HR`.

## 2. Calculated columns (Modeling → New column)
```DAX
Left = IF(HR[Attrition] = "Yes", 1, 0)

Age Group =
SWITCH(
    TRUE(),
    HR[Age] < 25, "Under 25",
    HR[Age] < 35, "25-34",
    HR[Age] < 45, "35-44",
    HR[Age] < 55, "45-54",
    "55+"
)

Tenure Band =
SWITCH(
    TRUE(),
    HR[YearsAtCompany] <= 1, "0-1 yrs",
    HR[YearsAtCompany] <= 4, "2-4 yrs",
    HR[YearsAtCompany] <= 9, "5-9 yrs",
    "10+ yrs"
)
```

## 3. Measures (Modeling → New measure)
```DAX
Headcount = COUNTROWS(HR)

Attrition Count = CALCULATE(COUNTROWS(HR), HR[Attrition] = "Yes")

Attrition Rate = DIVIDE([Attrition Count], [Headcount], 0)

Avg Monthly Income = AVERAGE(HR[MonthlyIncome])

Avg Tenure (Years) = AVERAGE(HR[YearsAtCompany])

Avg Job Satisfaction = AVERAGE(HR[JobSatisfaction])

Overtime Rate =
DIVIDE(CALCULATE(COUNTROWS(HR), HR[OverTime] = "Yes"), [Headcount], 0)
```
Format `Attrition Rate` and `Overtime Rate` as percentages.

## 4. Page layout
| Area | Visual | Fields |
|---|---|---|
| Top row | 5 Card visuals | Headcount, Attrition Rate, Avg Monthly Income, Avg Tenure (Years), Avg Job Satisfaction |
| Left | Clustered column chart | Axis: Department, Values: Attrition Rate |
| Middle | Clustered column chart | Axis: OverTime, Values: Attrition Rate |
| Right | Clustered column chart | Axis: Age Group, Values: Attrition Rate |
| Bottom left | Clustered column chart | Axis: Tenure Band, Values: Attrition Rate |
| Bottom middle | Clustered column chart | Axis: JobSatisfaction, Values: Attrition Rate |
| Bottom right | Bar chart | Axis: JobRole, Values: Avg Monthly Income |
| Side panel | Slicers | Department, Gender, OverTime |

Tip: sort the `Age Group` and `Tenure Band` axes by a numeric helper column (or use "Sort by column") so they appear in age/tenure order rather than alphabetically.

## 5. Publish
Take a screenshot of the finished report and save it to `powerbi/` (for example `powerbi_dashboard.png`), then reference it in the README. You can also commit the `.pbix` file if it is small.
