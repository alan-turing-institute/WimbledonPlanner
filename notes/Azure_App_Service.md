# Creating a Web App on Azure

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

### Create a key vault

### Authorise the web app to access the key vault

### Pass secrets to the web app container

## Creating a docker image

## Updating the image on the web app
