include build/test/.env.test

MIGRATION_COMPOSE=build/migrations/compose.yaml
DEV_COMPOSE=build/dev/compose.yaml
PROD_COMPOSE=build/prod/compose.yaml
TESTS_COMPOSE=build/test/compose.yaml
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

#-------------------------------------------------------------------------------------------------

tracker.test.build:
	@docker compose -f ${TESTS_COMPOSE} build

tracker.test_db.start:
	@docker compose -f ${TESTS_COMPOSE} up -d test_tracker_db
	@until docker compose -f ${TESTS_COMPOSE} exec test_tracker_db pg_isready -U ${POSTGRES_USER}; do sleep 1; done

tracker.test.integration: tracker.test.build tracker.test_db.start
	@docker compose -f ${TESTS_COMPOSE} run --rm test_tracker_app pytest -v ${INTEGRATION_TESTS_PATH}; docker compose -f ${TESTS_COMPOSE} down

tracker.test.unit: tracker.test.build
	@docker compose -f ${TESTS_COMPOSE} run --rm test_tracker_app pytest -v ${UNIT_TESTS_PATH}

tracker.test.full: tracker.test.build tracker.test_db.start
	@docker compose -f ${TESTS_COMPOSE} run --rm test_tracker_app pytest -v ${TESTS_PATH}; docker compose -f ${TESTS_COMPOSE} down