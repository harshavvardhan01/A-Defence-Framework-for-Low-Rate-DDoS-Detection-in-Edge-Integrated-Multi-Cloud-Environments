#  A DynamoDB table storing one item per federated round,
#       keyed by round number, as a durable alternative to the
#       coordinator's local JSON state file.
# The local file is lost if the coordinator's disk is
#       lost. DynamoDB persists independently of any single
#       instance, matching the production design target
#       already named in Table 1 of the Design chapter.

resource "aws_dynamodb_table" "appcd_round_state" {
  name         = "appcd-round-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "round_number"

  attribute {
    name = "round_number"
    type = "N"
  }

  tags = { Name = "appcd-round-state" }
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.appcd_round_state.name
}