#!/bin/bash

SERVER_PORT=${1-5000}
export SERVER_PORT=${SERVER_PORT}
export AUTH0_DOMAIN=https://login-sandbox.sensynehealth.com/
export AUTH0_AUDIENCE=https://dev.sensynehealth.com/
export AUTH0_METADATA=https://gdm.sensynehealth.com/metadata
export AUTH0_JWKS_URL=https://login-sandbox.sensynehealth.com/.well-known/jwks.json
export AUTH0_CLIENT_ID=someclientid
export GRANT_TYPE=http://auth0.com/oauth/grant-type/password-realm
export CUSTOMER_CODE=DEV
export IGNORE_JWT_VALIDATION=True
export TOKEN_URL=https://login-sandbox.sensynehealth.com/oauth/token
export AUTH0_MGMT_CLIENT_ID=someid
export AUTH0_MGMT_CLIENT_SECRET=secret
export AUTH0_AUTHZ_CLIENT_ID=someid
export AUTH0_AUTHZ_CLIENT_SECRET=secret
export AUTH0_AUTHZ_WEBTASK_URL=https://draysonhealth-sandbox.eu.webtask.io/someid/api
export AUTH0_CLIENT_ID=someid
export NONCUSTOM_AUTH0_DOMAIN=https://draysonhealth-sandbox.eu.auth0.com
export ENVIRONMENT=DEVELOPMENT
export ALLOW_DROP_DATA=True
export PROXY_URL=http://localhost
export HS_KEY=secret
export FLASK_APP=dhos_janitor_api/autoapp.py
export DHOS_ACTIVATION_AUTH_API=http://dhos-activation-auth
export DHOS_AUDIT_API=http://dhos-audit
export DHOS_ENCOUNTERS_API=http://dhos-encounters
export DHOS_FUEGO_API=http://dhos-fuego
export DHOS_LOCATIONS_API=http://dhos-locations
export DHOS_MEDICATIONS_API=http://dhos-medications
export DHOS_MESSAGES_API=http://dhos-messages
export DHOS_OBSERVATIONS_API=http://dhos-observations
export DHOS_QUESTIONS_API=http://dhos-questions
export DHOS_SERVICES_API=http://dhos-services
export DHOS_TELEMETRY_API=http://dhos-telemetry
export DHOS_TRUSTOMER_API=http://dhos-trustomer
export DHOS_URL_API=http://dhos-url
export GDM_ARTICLES_API=http://gdm-articles
export GDM_BG_READINGS_API=http://bg-readings
export GDM_BFF=http://gdm-bff
export SEND_BFF=http://send-bff
export DISABLE_AUTH0_JWT_FETCH=True
export REDIS_INSTALLED=False
export CUSTOMER_CODE=dev
export POLARIS_API_KEY=secret
export LOG_LEVEL=DEBUG
export LOG_FORMAT=colour


if [ -z "$*" ]
then
  python -m dhos_janitor_api
else
  flask $*
fi
