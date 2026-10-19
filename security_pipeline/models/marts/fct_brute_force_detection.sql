with failed_logins as (

    select
        event_id,
        event_timestamp,
        user_id,
        ip_address,
        user_agent,
        row_number() over (
            partition by user_id, ip_address
            order by event_timestamp
        ) as attempt_number,
        count(*) over (
            partition by user_id, ip_address
            order by event_timestamp
            range between interval '10 minutes' preceding and current row
        ) as failures_in_window,
        event_timestamp - lag(event_timestamp) over (
            partition by user_id, ip_address
            order by event_timestamp
        ) as time_since_last_attempt
    from {{ ref('stg_auth_events') }}
    where event_type = 'FAILED_LOGIN'
      and status = 'FAILURE'

),
brute_force_candidates as (

    select
        *,
        case
            when failures_in_window >= 5 then true
            else false
        end as is_brute_force
    from failed_logins

)

select
    event_id,
    event_timestamp,
    user_id,
    ip_address,
    user_agent,
    attempt_number,
    failures_in_window,
    time_since_last_attempt,
    is_brute_force
from brute_force_candidates
where is_brute_force = true
order by user_id, ip_address, event_timestamp