with source as (

    select * from {{ source('raw', 'auth_events') }}

),

cleaned as (

    select
        id as event_id,
        case
            when event_timestamp ~ '^\d{2}/\d{2}/\d{4}'
                then to_timestamp(event_timestamp, 'MM/DD/YYYY HH24:MI:SS')
            else event_timestamp::timestamp
        end as event_timestamp,
        lower(trim(user_id)) as user_id,
        upper(trim(event_type)) as event_type,
        case
            when trim(ip_address) = '' then null
            else trim(ip_address)
        end as ip_address,
        upper(trim(status)) as status,
        trim(user_agent) as user_agent
    from source
    where event_timestamp is not null

),
deduplicated as (

    select distinct on (event_timestamp, user_id, event_type, ip_address)
        event_id,
        event_timestamp,
        user_id,
        event_type,
        ip_address,
        status,
        user_agent
    from cleaned
    order by event_timestamp, user_id, event_type, ip_address, event_id

)

select * from deduplicated