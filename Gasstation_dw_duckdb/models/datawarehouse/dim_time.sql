select
    h as time_key,
    h as hour_24,
    case
        when h between 5 and 10  then 'Morning (05-10)'
        when h between 11 and 13 then 'Midday (11-13)'
        when h between 14 and 17 then 'Afternoon (14-17)'
        when h between 18 and 21 then 'Evening (18-21)'
        else 'Night (22-04)'
    end as day_part
from range(0, 24) as t(h)