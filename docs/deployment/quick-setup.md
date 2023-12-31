# Quick Setup

!!! warning "You need to have installed [Docker](https://docs.docker.com/get-docker/)"

**Step 1:** Clone the [repo](https://github.com/IDinsight/aaq-core) to your machine

    git clone git@github.com:IDinsight/aaq-core.git

**Step 2:** Navigate to the `deployment/` subfolder.

**Step 3:** Copy `template.env` to `.env` and edit it to set the
variables.

    POSTGRES_PASSWORD=
    OPENAI_API_KEY=
    QUESTION_ANSWER_SECRET=
    ...

!!! note "Check out `template.env` for a full list of environment variables to be set."

**Step 4:** Copy `template.env.nginx` to `.env.nginx` and edit it to set the variables

    DOMAIN=
    MAIL=
    ...

!!! note "Check out `template.env.nginx` for a full list of environment variables to be set."

**Step 5:** Run `init-letsencrypt.sh` to get an SSL certificate from LetsEncrypt

    chmod a+x ./init-letsencrypt.sh
    ./init-letsencrypt.sh

**Step 6:** Run docker-compose

    docker compose -f docker-compose.yml -f docker-compose.dev.yml -p aaq-stack up -d --build

You can now access the admin app at `https://[DOMAIN]/` and the apis at `https://[DOMAIN]/api`

!!! note "To test the endpoints, see [Calling the endpoints](../develop/testing.md#call-the-endpoints)."

**Step 7:** Shutdown containers

    docker compose -f docker-compose.yml -f docker-compose.dev.yml -p aaq-stack down
