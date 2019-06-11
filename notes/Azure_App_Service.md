# Creating a Web App on Azure

The instructions below assume you already have a GitHub repo containing a script that runs some kind of app/local server which you want to host on the web with Azure.

## Create an App Service

"App Service" on Azure is the way to create Azure web apps. To create one:

1. Go to the [Azure portal](https://portal.azure.com)
1. Search for "App Services" or select it from the menu on the left.
1. Click Add or Create app service
1. Choose a subscription, resource group and name. Your web-site will be `<NAME>.azurewebsites.net`.
1. Choose to publish a `Docker image` running on `Linux`. If you only need to run simple code (e.g. you only need pip installable packages) you can choose a code app service instead, which uses one of the readymade docker images defined [here](https://github.com/Azure-App-Service/python) (for python). For wimbledon this didn't work as:
   1. The default container doesn't have git installed, and wimbledon requires some python packages to be installed via `pip install git+<repo>`.
   1. Wimbledon requires some command-line tools, e.g. `wkhtmltopdf`.
1. Pick region (e.g. Western Europe)
1. Pick/create a new App Service plan - this is the resources assigned to the web app server. Click on "change size" to configure.
1. Click Review & Create
1. Once created, you should now see your web app in the App Services list.

## Network Configuration

The wimbledon-planner app has been set to only allow connections from the Turing. To do this:

1. Go to your app service's page in the Azure portal. 
1. Click `Networking` in the menu on the left (under Settings).
1. Click `Configure Access Restrictions` (under Access Restrictions).
1. For `193.60.220.240` (Turing LAN) and `193.60.220.253` (Turing WiFi) click `Add Rule` and add an allow rule.
1. On the `<NAME>.scm.azurewebsites.net` tab tick "Same restrictions as `<NAME>.azurewebsites.net`".

## Passing Secrets to the Container from a Key Vault

You may need the container to have access to tokens or other secrets (e.g. Harvest/Forecast credentials for the wimbledon web app). These can be passed to the web app container from a key vault without them needing to be typed anywhere in code.

### Create a system managed identity for the web-app

1. Go to your app service's overview page in the Azure portal.
1. Click `Identity` (under Settings in the menu on the left).
1. Set the Status of the System Assigned identify to On.
1. You should now be able to find your app in Azure active directory. For me I found it under Azure Active Directory -> Enterprise Applictions -> Application Type: All Applications.

### Create a key vault and add secrets to it

1. Search for and go to the Key Vaults page in Azure portal.
1. Click Add and create a new key vault with appropriate name, resource group, subscription etc. for your application.
1. Once created, browse to your new Key Vault.
1. Click Secrets in the lefthand menu.
1. Click Generate/Import
1. Choose Upload Options: manual, give the secret a name, and paste the paste the secret value (e.g. password/token) into the value field.
1. Click Create.
1. Repeat for other secrets.

### Authorise the web app to access the key vault

1. From your Key Vault page in the portal, click on Access Control (IAM) in the lefthand menu.
1. Click Add
1. Choose the "Reader" role.
1. Under "Assign access to" pick "App Service".
1. Choose the subscription your app service is in.
1. Pick your app service from the list (if it doesn't appear - check you've done the create a system managed identity step above).
1. Click Save.
1. Click "Access Policies" in the menu on the left.
1. Click "Add New".
1. Search for your app under "Service principal".
1. Choose the permissions you want your app to have over secrets, keys and certificates in the key vault (e.g. get and list management operations only).
1. Click Ok.
1. Click Save.

### Pass secrets to the web app container

1. Browse to your app service's page in the Azure portal.
1. Click on configuration in the lefthand menu.
1. Click "New Application Setting".
1. The `Name` field defines the name of the environment variable that will be available in the container.
1. The `Value` field should take the following format: `@Microsoft.KeyVault(SecretUri=<YOUR_SECRET_URI>)`. To get the secret URI:
   1. Go to your Key Vault's page in the Azure portal.
   1. Click on Secrets in the lefthand menu.
   1. Click on the Secret you want to pass as an environment variable.
   1. Click on the version you want to use.
   1. Copy the URI from the "Secret Identifier" field.
1. Repeat for all secrets you want to be available in the container.

## Creating a Docker image on DockerHub

Your web app will run in a docker container on your Azure app service. The container setup is defined by the `Dockerfile`, by default a file with that name in the root folder of your repo. The `Dockerfile` defines the OS environment used in the image, e.g. some linux distribution and some python version, installation of any required tools, port setup, copying of files from the repo to the container, and the command to run after the container has been setup, e.g. to start the web server. 

For help with Dockerfiles see:
* [Docker documentation](https://docs.docker.com/get-started/)
* [Default Azure Python 3.7 Dockerfile](https://github.com/Azure-App-Service/python/blob/master/3.7.0/Dockerfile)
* [Wimbledon Planner Dockerfile](https://github.com/alan-turing-institute/WimbledonPlanner/blob/master/Dockerfile)

Your Docker images can be hosted on [DockerHub](https://hub.docker.com/). To do this:
1. Make a DockerHub account: https://hub.docker.com/signup
1. From your account page go to repositories and then click `Create Repository`. Give this the name you want and make it a **public repository** (if you need a private repository you'll need to figure out more authentication steps, plus may want to consider Azure container registry instead of Dockerhub).
1. Download and install Docker Desktop: https://www.docker.com/products/docker-desktop
1. To build your docker image locally, in the root folder of your repo (assuming you have your Dockerfile there), run `docker build . -t <DOCKERHUB_USERNAME>/<REPO_NAME>`
1. To push your (already built) docker image to the repo run `docker push <DOCKERHUB_USERNAME>/<REPO_NAME>`

## Configure the App Service to Use the Docker Image

1. Browse to your App Service's page in the Azure portal.
1. Click on "Container Settings" in the lefthand menu.
1. Select the "Single Container" tab.
1. Select "Docker Hub" as the Image source.
1. In the Image and optional tag field write: `<DOCKERHUB_USERNAME>/<REPO_NAME>:latest`.
1. Click Save.
1. The app service should now start to pull the Docker image and then run it - try refreshing the logs in the Container Settings page after a couple of minutes to see if something is happening. Once successful you should see a message along the lines of `Container <NAME>_0 for site <NAME> initialized successfully and is ready to serve requests.` If not try restarting (or manually stopping and then starting) the app service from its overview page in the portal.

## Updating the image on the web app

1. Run `docker build` and then `docker push` on the local copy of your repo (see "Creating a Docker image on DockerHub" section above for details).
1. Browse to your App Service's page in the Azure portal.
1. I've had some mixed success with triggering the App Service to update, but some combination of restarting, stopping, starting and browsing to the app service's url seems to force it to pull the new image.

## Set up Automated Docker builds and Azure deployment

You can set up DockerHub to rebuild your image whenever you make a new commit to master in yur GitHub repo, and also to trigger Azure to update the app service automatically when there is a new build available in docker hub. I have the automated build working, but not the automated redeployment on Azure (possibly as I've blocked all IPs except the Turing).

### To set up automated build on DockerHub:
1. Go to your account settings on DockerHub.
1. Under "Linked Accounts" click connect by GitHub, and follow through steps to authenticate DockerHub with your GitHub account.
1. Browse to your DockerHub repository.
1. Click on "Builds"
1. Click "Configure Automated Builds".
1. Pick the GitHub repository containing the Dockerfile you want to build from the dropdown lists.
1. If necessary, configure the settings (by default: rebuild on every commit to master).
1. Click Save.

Now if you make a new commit to your GitHub repo and then browse to your DockerHub repo, you should see a build pending (and then success/failure logs when done).

### To set up automated redeployment on Azure:
1. Browse to your app service's page in the Azure portal.
1. Click on "Container Settings" in the lefthand menu.
1. Set "Continuous Deployment" to "On" and copy the webhook URL.
1. Click "Save".
1. Browse to your DockerHub repository.
1. Click on "Webhooks"
1. Choose some meaningful name (e.g. "Azure") and paste the URL copied before into the webhook URL field.
1. Click the "+".

In principle DockerHub should now trigger your App Service to update whenever a new image build is available. For me the webhook always fails (can look at the history from the webhooks page on DockerHub), I suspect because I've only authenticated Turing IPs to access the App Service although DockerHub provides no way that I can see to debug why a webhook has failed.
