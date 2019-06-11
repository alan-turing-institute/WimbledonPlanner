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

## Creating a docker image

## Updating the image on the web app
