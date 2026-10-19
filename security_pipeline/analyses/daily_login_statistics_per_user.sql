SELECT user_id, event_date, total_attempts, failed_logins, failure_rate_pct
FROM analytics.fct_login_attempts
ORDER BY failure_rate_pct DESC
LIMIT 5;