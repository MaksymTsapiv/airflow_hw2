# Airflow Marketing Material Injection

### Set up

First build a custom airflow image:

```bash
chmod +x ./scripts/build_image.sh

./scripts/build_image.sh

```

Then add some environmental variables:

```bash

echo -e "AIRFLOW_UID=$(id -u)" > .env
echo "AIRFLOW_IMAGE_NAME=custom_airflow:2.7.3" >> .env

```

### Run

```bash
docker compose up
```

Then, go to the `localhost:8080`, create postgres connection `marketing_pg_conn`,
use `custom` as a user and a password.

You will also need to add `TARGET_URL` and `PDL_API_KEY` as variables, where `TARGET_URL`
is the url you want to get posters from, for example `https://www.whosmailingwhat.com/blog/best-direct-mail-marketing-examples/`

Run `marketing_hw2` dag.
