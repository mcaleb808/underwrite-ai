.PHONY: init plan apply destroy output fmt lint

STATE_BUCKET ?= $(shell sed -nE 's/^state_bucket = "(.*)"/\1/p' .backend-config 2>/dev/null)

init:
	@if [ -z "$(STATE_BUCKET)" ]; then \
		echo "Set STATE_BUCKET=<gcs-bucket> or create infra/.backend-config (see README)."; \
		exit 1; \
	fi
	terraform init -backend-config="bucket=$(STATE_BUCKET)" -backend-config="prefix=tf-state"

plan:
	terraform plan -var-file=terraform.tfvars

apply:
	terraform apply -var-file=terraform.tfvars

destroy:
	terraform destroy -var-file=terraform.tfvars

output:
	terraform output

fmt:
	terraform fmt -recursive

lint: fmt
	terraform validate
