IMAGE_NAME := eudg956/dockerfile-extract
FILES_DIR := k8s
image:
	docker build . -t $(IMAGE_NAME) -f $(FILES_DIR)/Dockerfile

ns:
	exists=$$(kubectl get ns red-hat --ignore-not-found); \
	if [ -z "$$exists" ]; then kubectl create ns red-hat; fi;

run: ns
	kubectl --namespace red-hat apply -f $(FILES_DIR)/job.yaml

log:
	pods=$$(kubectl --namespace red-hat get pods --selector=job-name=dockerfile.extract --output=jsonpath='{.items[*].metadata.name}'); \
	kubectl --namespace red-hat logs $$pods;
