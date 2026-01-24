MIGRATION_COMPOSE=build/migrations/compose.yaml

DEV_COMPOSE=build/dev/compose.yaml

PROD_COMPOSE=build/prod/compose.yaml

TESTS_COMPOSE=build/tests/compose.yaml
TESTS_PATH=tests
INTEGRATION_TESTS_PATH=${TESTS_PATH}/test_integration
UNIT_TESTS_PATH=${TESTS_PATH}/test_unit



tracker.network.setup:
	@docker network create MyTrackerNetwork >/dev/null 2>&1 || true; \
	docker network create tracker_migrations_network >/dev/null 2>&1 || true

#--------------------------------------------------------------------------------------

tracker.migrations.init:
	@cd build/migrations && alembic init -t async alembic


tracker.migrations.build: tracker.network.setup
	@docker compose -f ${MIGRATION_COMPOSE} build


tracker.migrations.new: tracker.migrations.build 
	@docker compose -f ${MIGRATION_COMPOSE} run --rm tracker_migrations alembic revision --autogenerate -m "${msg}"


tracker.migrations.up: tracker.migrations.build
	@docker compose -f ${MIGRATION_COMPOSE} run --rm tracker_migrations alembic upgrade head


tracker.migrations.down:
	@docker compose -f ${MIGRATION_COMPOSE} run --rm tracker_migrations alembic downgrade ${n}

#--------------------------------------------------------------------------------------

tracker.dev.build: tracker.network.setup
	@docker compose -f ${DEV_COMPOSE} build


tracker.dev.start:
	@docker compose -f ${DEV_COMPOSE} up


tracker.dev.build.start: tracker.dev.build
	@docker compose -f ${DEV_COMPOSE} up

tracker.dev.down:
	@docker compose -f ${DEV_COMPOSE} down