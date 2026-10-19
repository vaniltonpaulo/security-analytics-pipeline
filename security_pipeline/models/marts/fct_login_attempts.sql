with login_events as (

    select *
    from {{ ref('stg_auth_events') }}
    where event_type in ('LOGIN', 'FAILED_LOGIN')

),

user_daily_stats as (

    select
        user_id,
        date_trunc('day', event_timestamp)::date as event_date,
        count(*) as total_attempts,
        count(*) filter (where status = 'SUCCESS') as successful_logins,
        count(*) filter (where status = 'FAILURE') as failed_logins,
        count(distinct ip_address) as unique_ips,
        round(
            count(*) filter (where status = 'FAILURE')::numeric
            / nullif(count(*), 0) * 100,
            2
        ) as failure_rate_pct
    from login_events
    group by user_id, date_trunc('day', event_timestamp)::date

)

select
 -- generates a unique hash for each user-date combination.
    md5(user_id || '|' || event_date::text) as login_stat_id,
    user_id,
    event_date,
    total_attempts,
    successful_logins,
    failed_logins,
    unique_ips,
    failure_rate_pct
from user_daily_stats