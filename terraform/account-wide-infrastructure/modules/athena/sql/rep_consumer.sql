CREATE OR REPLACE VIEW "rep_consumer" AS
WITH
  cc AS (
   SELECT
     time
   , event_timestamp
   , date
   , host
   , event_log_reference
   , event_level
   , event_location
   , event_message
   , event_service
   , event_function_request_id
   , event_correlation_id
   , event_xray_trace_id
   , event_pointer_types
   , COALESCE("event_headers_nhsd-end-user-organisation-ods", event_metadata_ods_code) user_ods
   FROM
     consumer_countdocumentreference
)
, cr AS (
   SELECT
     time
   , event_timestamp
   , date
   , host
   , event_log_reference
   , event_level
   , event_location
   , event_message
   , event_service
   , event_function_request_id
   , event_correlation_id
   , event_xray_trace_id
   , event_pointer_types
   , COALESCE("event_headers_nhsd-end-user-organisation-ods", event_metadata_ods_code) user_ods
   FROM
     consumer_readdocumentreference
)
, cs AS (
   SELECT
     time
   , event_timestamp
   , date
   , host
   , event_log_reference
   , event_level
   , event_location
   , event_message
   , event_service
   , event_function_request_id
   , event_correlation_id
   , event_xray_trace_id
   , event_pointer_types
   , COALESCE("event_headers_nhsd-end-user-organisation-ods", event_metadata_ods_code) user_ods
   FROM
     consumer_searchdocumentreference
)
, csp AS (
   SELECT
     time
   , event_timestamp
   , date
   , host
   , event_log_reference
   , event_level
   , event_location
   , event_message
   , event_service
   , event_function_request_id
   , event_correlation_id
   , event_xray_trace_id
   , event_pointer_types
   , COALESCE("event_headers_nhsd-end-user-organisation-ods", event_metadata_ods_code) user_ods
   FROM
     consumer_searchpostdocumentreference
)
, base AS (
   SELECT *
   FROM
     cc
UNION    SELECT *
   FROM
     cr
UNION    SELECT *
   FROM
     cs
UNION    SELECT *
   FROM
     csp
)
, ods_codes AS (
   SELECT DISTINCT
     user_ods
   , event_xray_trace_id
   FROM
     base
   WHERE (user_ods IS NOT NULL)
)
SELECT
  time
, event_timestamp
, date
, host
, event_log_reference
, event_level
, event_location
, event_message
, event_service
, event_function_request_id
, b.event_correlation_id
, b.event_xray_trace_id
, event_pointer_types
, oc.user_ods
FROM
  (base b
LEFT JOIN ods_codes oc ON (b.event_xray_trace_id = oc.event_xray_trace_id))
