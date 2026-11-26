-- Average and median time to close each issue type.
-- Open issues are counted separately and are not included in resolution time.
SELECT
    issue_type,
    COUNT(*) FILTER (WHERE status = 'Resolved') AS resolved_issues,
    COUNT(*) FILTER (WHERE status = 'Open') AS open_issues,
    ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - opened_at)) / 3600.0)
        FILTER (WHERE status = 'Resolved'), 1) AS average_resolution_hours,
    ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (resolved_at - opened_at)) / 3600.0
    ) FILTER (WHERE status = 'Resolved'))::numeric, 1) AS median_resolution_hours
FROM issues
GROUP BY issue_type
ORDER BY average_resolution_hours DESC NULLS LAST;
