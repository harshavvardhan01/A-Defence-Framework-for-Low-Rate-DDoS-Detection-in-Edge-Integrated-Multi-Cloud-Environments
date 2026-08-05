# providers.tf
#
# WHAT: Declares AWS as our infrastructure provider, and sets
#       up TWO separate provider configurations — one per
#       region — since Terraform needs to know explicitly
#       which region each resource belongs to.
# WHY:  Your architecture is deliberately two-region. Terraform
#       represents "a second region" as a second labeled
#       provider block (an "alias"), not a special resource
#       type — this is the standard way Terraform expresses
#       multi-region infrastructure.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Primary region — Ireland (Dublin)
provider "aws" {
  region = "eu-west-1"
}

# Secondary region — N. Virginia, explicitly aliased so we
# can reference it separately from the primary
provider "aws" {
  alias  = "secondary"
  region = "us-east-1"
}