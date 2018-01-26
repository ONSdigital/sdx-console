import testing.postgresql
import console.settings

Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=False)
postgresql = Postgresql()
console.settings.DB_URI = postgresql.url()
