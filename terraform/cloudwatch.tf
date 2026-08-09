# A CloudWatch Log Group to receive coordinator and
#       edge-agent container output, plus an alarm watching
#       for the specific ERROR-level pattern for kill-node
#       test already produces ("node X FAILED this round").
#Centralised, durable logging independent of any single
#       instance's disk or docker logs buffer -- and a real,
#       AWS-native confirmation of the same failure event for
#       application-level fault-tolerance test already proves.

resource "aws_cloudwatch_log_group" "appcd_logs" {
  name              = "/appcd/containers"
  retention_in_days = 7

  tags = { Name = "appcd-logs" }
}

resource "aws_cloudwatch_log_metric_filter" "node_failure_filter" {
  name           = "appcd-node-failures"
  log_group_name = aws_cloudwatch_log_group.appcd_logs.name
  pattern        = "\"FAILED this round\""

  metric_transformation {
    name      = "NodeFailureCount"
    namespace = "APPCD"
    value     = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_metric_alarm" "node_failure_alarm" {
  alarm_name          = "appcd-node-failure-detected"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods   = 1
  metric_name          = "NodeFailureCount"
  namespace            = "APPCD"
  period               = 60
  statistic            = "Sum"
  threshold            = 1
  alarm_description    = "Fires when the coordinator logs a node failure during a federated round -- the same event exercised by the manual kill-node fault-tolerance test."
  treat_missing_data   = "notBreaching"
}