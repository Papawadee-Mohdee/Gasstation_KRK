select range::integer as hour_id, case when range < 8 then '00-07' when range < 16 then '08-15' else '16-23' end as time_band from range(24)
