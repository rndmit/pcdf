KUBEMODELS_SCHEMA 		:= https://github.com/kubernetes/kubernetes/raw/release-1.28/api/openapi-spec/swagger.json
LOCAL_DIR 				:= .local

KUBEMODELS_PKG_DIR 		= ${LOCAL_DIR}/pkg/kubemodels
KUBEMODELS_PKG_NAME 	= kubemodels
POETRY_FLAGS			= -q --no-ansi --no-interaction

DOCS_SRC_DIR	= "docs"
DOCS_BUILD_DIR	= ".local/docs"

COLOR_GREEN		=\033[0;32m
COLOR_RED		=\033[0;31m
COLOR_BLUE		=\033[0;34m
COLOR_END		=\033[0m

define log:success
	@echo "$(COLOR_GREEN)OK$(COLOR_END)"
endef

define log:error
	$(eval $@_ERR = $(1))
	@echo "$(COLOR_RED)Failed: ${$@_ERR} $(COLOR_END)"
	@exit 1
endef

clean:
	@echo "- Clean ${LOCAL_DIR}"
	@rm -rf ${LOCAL_DIR}
	@mkdir -p ${LOCAL_DIR}
	$(call log:success)

kubemodels-schema:
	@echo "- Downloading kubemodels schema"
	@curl -s -o "${LOCAL_DIR}/kubeschema.json" -L "${KUBEMODELS_SCHEMA}"
	$(call log:success)

kubemodels-generate: kubemodels-schema
	@echo "- Generating kubemodels package"
	@mkdir -p ${LOCAL_DIR}/pkg
	@poetry ${POETRY_FLAGS} new --name ${KUBEMODELS_PKG_NAME} ${KUBEMODELS_PKG_DIR}
	@datamodel-codegen --input ${LOCAL_DIR}/kubeschema.json \
		--output ${KUBEMODELS_PKG_DIR}/kubemodels \
		--input-file-type jsonschema \
		--output-model-type pydantic_v2.BaseModel \
		--enum-field-as-literal all \
		--use-field-description
	$(call log:success)

kubemodels-install:
	@echo "- Installing kubemodels package"
	@echo "-- Removing ${KUBEMODELS_PKG_NAME} if exists"
	@poetry -q ${POETRY_FLAGS} remove ${KUBEMODELS_PKG_NAME} \
		|| echo "-- Seems like ${KUBEMODELS_PKG_NAME} not installed. It's OK"; true
	@echo "-- Installing local ${KUBEMODELS_PKG_NAME} package"
	@poetry -q ${POETRY_FLAGS} add ${KUBEMODELS_PKG_DIR}
	$(call log:success)

kubemodels: kubemodels-generate kubemodels-install

.PHONY: docs
docs:
	@echo "- Generating docs"
	@poetry install
	@sphinx-apidoc -f -o ${DOCS_SRC_DIR}/api pcdf/
	@sphinx-build ${DOCS_SRC_DIR} ${DOCS_BUILD_DIR}
	$(call log:success)