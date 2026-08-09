# Configurable values — instance size, your SSH key
#       name, your IP for security group rules.
# Keeping these separate means changing them later
#       doesn't require touching the actual infrastructure
#       logic — you only edit this one file.

variable "instance_type" {
  description = "EC2 instance size for all 4 nodes"
  type        = string
  default     = "t3.small"
}

variable "appcd_token" {
  description = "Shared auth token for edge agents and coordinator"
  type        = string
  default     = "dev-token-change-me"
  sensitive   = true
}

variable "my_ip" {
  description = "Your current public IP, for SSH access rules"
  type        = string
  # We'll fill this in Step 4 below
}