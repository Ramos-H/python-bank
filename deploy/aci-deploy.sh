#!/bin/bash
set -e

IMAGE=$1
if [ -z "$IMAGE" ]; then
    echo "Error: Image argument is required"
    exit 1
fi

RESOURCE_GROUP=${RESOURCE_GROUP:-"qr-payment-rg"}
ACI_GROUP_NAME=${ACI_GROUP_NAME:-"qr-payment-test-group"}
LOCATION=${LOCATION:-"eastus"}

echo "Deploying container group to Azure Container Instances..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Group Name: $ACI_GROUP_NAME"
echo "Target Image: $IMAGE"

# Create the resource group if it doesn't exist
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" || true

# Deploy the multi-container group using the template and overriding the banking image
az container create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACI_GROUP_NAME" \
    --file ./deploy/aci-deployment.yaml \
    --set-value spec.containers[0].image="$IMAGE"

echo "ACI Deployment complete."
