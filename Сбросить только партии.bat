cd e:\Cursor\SeaBattle
docker compose exec redis redis-cli DEL seabattle:registry:slots
docker compose exec redis redis-cli --scan --pattern "seabattle:session:*"